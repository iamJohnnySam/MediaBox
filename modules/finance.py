import os
import re
import shutil
from datetime import datetime

import global_variables
import refs
from brains.job import Job
from communication.message import Message
from database_manager.sql_connector import SQLConnector
from modules.base_module import Module
from tools.custom_exceptions import InvalidParameterException
from tools.logger import log


class Finance(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        self.db_finance = SQLConnector(job.job_id, database=refs.db_finance)

    def sms(self):
        success, sms = self.check_value(index=-1, description="sms received from bank.")
        if not success:
            return

        sms = str(sms).lower()

        # Extract value
        try:
            value_match = str(re.findall(r'lkr (\d+\.\d{2})', sms)[0]).replace("lkr ", "")
        except IndexError:
            value_match = str(re.findall(r'(?:rs\.|lkr)\s?(?:\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)', sms)[0])
            value_match = value_match.replace("lkr ", "").replace("rs. ", "").replace(",", "").strip()
        log(job_id=self._job.job_id, msg=f"Transaction amount: {value_match}")
        value_match.replace("lkr ", "").replace("rs.  ", "").replace(",", "").strip()
        self._job.collect(value_match, 0)

        # Check Transaction Type
        if any(x.lower() in sms for x in global_variables.credit_words):
            self._job.collect('income', 1)
        elif any(x.lower() in sms for x in global_variables.debit_words):
            self._job.collect('expense', 1)
        else:
            raise InvalidParameterException(f"Could not find transaction type in {sms}")

        # Extract date
        try:
            date_match = str(re.findall(r'(\d{2}[/-]\d{2}[/-]\d{4})', sms)[0])
            log(job_id=self._job.job_id, msg=f"Date: {date_match}")
        except IndexError:
            date_match = datetime.today().strftime('%Y-%m-%d')
        self._job.collect(date_match, 2)

        # Extract vendor
        try:
            # vendor_match = str(re.findall(r'at ([^.0-9]+?)(?=\s\d+|[.])', sms)[0])
            vendor_match = str(re.findall(r'at ([^.0-9]+?)(?=\s\d+ [A-Z]{2}|$|[.]| on)', sms)[0])
            vendor_match = re.sub(' +', ' ', vendor_match)
            log(job_id=self._job.job_id, msg=f"Vendor: {vendor_match}")
        except IndexError:
            vendor_match = ""
        self._job.collect(vendor_match.strip(), 3)

        self._job.function = "finance"
        self.finance()

    def finance(self):
        # 0 - value
        # 1 - expense / income
        # 2 - date
        # 3 - raw vendor
        # 4 - vendor
        # 5 - duplicate?
        # 6 - category Type
        # 7 - category
        # todo user_id

        index = 0
        success, t_value = self.check_value(index=index, description="transaction amount",
                                            check_float=True, replace_str="lkr")
        if not success:
            return

        index = 1
        success, t_date = self.check_value(index=index, description="transaction date",
                                           check_date=True, default=datetime.today().strftime('%Y-%m-%d'))
        if not success:
            return

        index = 2
        success, t_type = self.check_value(index=index, description="transaction type",
                                           check_list=["income", "expense"])
        if not success:
            return

        index = 3
        success, raw_vendor = self.check_value(index=index, description="vendor name")
        if not success:
            return

        index = 4
        default_vendor, options = self._get_from_lookup(raw_vendor, index,
                                                        refs.tbl_fin_raw_vendor, "vendor_id", "raw_vendor",
                                                        refs.tbl_fin_vendor, "name", "vendor_id")
        success, vendor = self.check_value(index=index, description="proper vendor name", default=default_vendor,
                                           check_list=options, manual_option=True)
        if not success:
            return
        vendor_id = self._fill_lut(raw_vendor, vendor,
                                   refs.tbl_fin_raw_vendor, "raw_vendor", "vendor_id",
                                   refs.tbl_fin_vendor, "name", "vendor_id")

        index = 5
        check_duplicate = self.db_finance.check_exists(refs.tbl_fin_trans, where={"date": t_date,
                                                                                  "amount": t_value,
                                                                                  "vendor_id": vendor_id})
        if check_duplicate == 0:
            default_duplicate = "yes"
        else:
            default_duplicate = None
        success, duplicate = self.check_value(index=index, description="yes if you want to continue. Duplicate exists.",
                                              default=default_duplicate,
                                              check_list=['yes'])
        if not success:
            return

        index = 6
        pre_sel_cats_str = self.db_finance.select(refs.tbl_fin_vendor, "category_id", where={"vendor_id": vendor_id})
        if pre_sel_cats_str is not None and pre_sel_cats_str[0] is not None:
            pre_sel_cat_ids = pre_sel_cats_str[0].split(";")
        else:
            pre_sel_cat_ids = []

        pre_sel_cats = []
        if self.check_index() <= index:
            for pre_sel_cat_id in pre_sel_cat_ids:
                pre_sel_cats.append(self.db_finance.select(refs.tbl_fin_cat,
                                                           "category",
                                                           where={"category_id": pre_sel_cat_id})[0])

        if not pre_sel_cats:
            all_cats = self.db_finance.select(refs.tbl_fin_cat, "category", where={"in_out": t_type}, fetch_all=True)
            pre_sel_cats = [x[0] for x in all_cats]

        success, cat = self.check_value(index=index, description="category of transaction",
                                        check_list=pre_sel_cats)
        if not success:
            return

        index = 7
        cat_id = self.db_finance.select(refs.tbl_fin_cat, "category_id", where={"category": cat})[0]
        if cat_id not in pre_sel_cats_str:
            pre_sel_cat_ids.append(str(cat_id))
            new_cat_ids = ';'.join(pre_sel_cat_ids)
            self.db_finance.update(refs.tbl_fin_vendor, {"category_id": new_cat_ids}, {"vendor_id": vendor_id})

        success, cat_id = self.check_value(index=index, description="category ID", default=cat_id, check_int=True)
        if not success:
            return

        self.db_finance.insert(refs.tbl_fin_trans,
                               "transaction_by, date, type, category_id, amount, vendor_id, vendor, photo_id",
                               (self._job.chat_id, t_date, t_type, cat_id, t_value, vendor_id, vendor,
                                ";".join([str(ele) for ele in self._job.photo_ids])))
        send_string = f"{str(t_type).capitalize()} added to {cat} ({cat_id}) for LKR {t_value} with {vendor} " \
                      f"({vendor_id})."
        log(self._job.job_id, msg=send_string)
        self.send_message(Message(send_string=send_string))
        self._job.complete()

        # todo add another option with the same params

    def _get_from_lookup(self, item, index,
                         raw_table, raw_id, raw_lookup,
                         lut_table, lut_column, lut_id):

        item = ''.join(letter for letter in item if (letter.isalnum() or letter.isspace()))
        item = re.sub(' +', ' ', item)

        default_id = self.db_finance.select(table=raw_table,
                                            columns=raw_id,
                                            where={raw_lookup: item})

        if default_id is not None:
            options = [self.db_finance.select(lut_table, lut_column, where={lut_id: default_id[0]})[0]]
        elif self.check_index() > index and self.get_index(index) != "":
            options = [self.get_index(index)]
        elif item == "":
            options = None
        else:
            cond = ""
            for item_part in str(item).split(" "):
                pre_sym = '' if len(item_part) < 3 else '%'
                filler = "" if cond == "" else " OR "
                cond = cond + filler + f'{lut_column} LIKE "{pre_sym}{item_part}%"'
            lut_options = self.db_finance.select(lut_table, lut_column, where=cond, fetch_all=True)
            options = [x[0] for x in lut_options] if lut_options is not None else None
        log(job_id=self._job.job_id, msg=f"Options: {options}")

        default = default_id[0] if default_id is not None else None

        return default, options

    def _fill_lut(self, raw_item, item,
                  raw_table, raw_column, raw_id,
                  lut_table, lut_column, lut_id):

        vendor_exists = self.db_finance.check_exists(table=lut_table, where={lut_column: item})
        if vendor_exists == 0:
            vendor_id = self.db_finance.insert(lut_table, lut_column, (item,))
        else:
            vendor_id = self.db_finance.select(lut_table, lut_id, where={lut_column: item})[0]

        raw_vendor_exists = self.db_finance.check_exists(raw_table, where={raw_column: raw_item})
        if raw_vendor_exists == 0:
            self.db_finance.insert(refs.tbl_fin_raw_vendor, f"{raw_column}, {raw_id}", (raw_item, vendor_id))

        return vendor_id

    def finance_photo(self):
        if not os.path.exists(refs.finance_images):
            os.makedirs(refs.finance_images)

        for value in self._job.photo_ids:
            shutil.move(os.path.join(refs.telepot_image_dump, value),
                        os.path.join(refs.finance_images, value))

        # todo OCR
