import os
import re
import shutil
from datetime import datetime

import global_variables
import refs
from brains.job import Job
from database_manager.sql_connector import sql_databases
from modules.base_module import Module
from tools.custom_exceptions import InvalidParameterException


class Finance(Module):
    def __init__(self, job: Job):
        super().__init__(job)

        self.db_finance = sql_databases[refs.db_finance]

    def sms(self):
        success, sms = self.check_value(index=-1, description="sms received from bank.")
        if not success:
            return

        sms = str(sms).lower()

        # Extract value
        value_match = str(re.findall(r'lkr (\d+\.\d{2})', sms)[0]).replace("lkr ", "")
        self._job.collect(value_match, 0)

        # Check Transaction Type
        if any(x.lower() in sms for x in global_variables.credit_words):
            self._job.collect('income', 1)
        elif any(x.lower() in sms for x in global_variables.debit_words):
            self._job.collect('expense', 0)
        else:
            raise InvalidParameterException(f"Could not find transaction type in {sms}")

        # Extract date
        date_match = str(re.findall(r'(\d{2}[/-]\d{2}[/-]\d{4})', sms)[0])
        if date_match == "":
            date_match = datetime.today().strftime('%Y-%m-%d')
        self._job.collect(date_match, 2)

        # Extract vendor
        vendor_match = str(re.findall(r'at ([^.]+)\.', sms)[0])
        self._job.collect(vendor_match, 3)

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

        index = 0
        success, value = self.check_value(index=index, description="transaction amount",
                                          check_float=True, replace_str="lkr")
        if not success:
            return

        index = 1
        success, t_type = self.check_value(index=index, description="transaction type",
                                           option_list=["income", "expense"])
        if not success:
            return

        index = 2
        success, t_date = self.check_value(index=index, description="transaction date",
                                           check_date=True, default=datetime.today().strftime('%Y-%m-%d'))
        if not success:
            return

        index = 3
        success, raw_vendor = self.check_value(index=index, description="vendor name")
        if not success:
            return

        index = 4
        query = f'SELECT vendor_id FROM {refs.tbl_fin_raw_vendor} WHERE raw_vendor="{raw_vendor}";'
        vendor_name = self.db_finance.run_sql(query=query, job_id=self._job.job_id)[0]
        if vendor_name != '':
            options = [vendor_name]
        elif len(self._job.collection) <= index and self._job.collection[index] != "":
            options = [self._job.collection[index]]
        else:
            cond = ""
            for ven_name in str(raw_vendor).split(" "):
                filler = "" if cond == "" else " OR "
                cond = cond + filler + f'name LIKE "%{ven_name}%"'
            query = f'SELECT name FROM {refs.tbl_fin_vendor} WHERE {cond}";'
            options = [x[0] for x in self.db_finance.run_sql(query=query, fetch_all=True, job_id=self._job.job_id)]
        success, vendor = self.check_value(index=index, description="proper vendor name", default=vendor_name,
                                           option_list=options)
        if not success:
            return
        query = f'SELECT COUNT(1) FROM {refs.tbl_fin_vendor} WHERE name="{vendor}";'
        vendor_exists = self.db_finance.run_sql(query=query, job_id=self._job.job_id)
        if vendor_exists == 0:
            success, vendor_id = self.db_finance.insert(refs.tbl_fin_vendor, "name", (vendor,))
        else:
            query = f'SELECT vendor_id FROM {refs.tbl_fin_vendor} WHERE name="{vendor}";'
            vendor_id = self.db_finance.run_sql(query=query, job_id=self._job.job_id)[0]
        query = f'SELECT COUNT(1) FROM {refs.tbl_fin_raw_vendor} WHERE raw_vendor="{raw_vendor}";'
        raw_vendor_exists = self.db_finance.run_sql(query=query, job_id=self._job.job_id)
        if raw_vendor_exists == 0:
            self.db_finance.insert(refs.tbl_fin_raw_vendor, "raw_vendor, vendor_id", (raw_vendor, vendor_id))

        index = 5
        # todo check duplicates

        index = 6
        if vendor_exists != 0:
            # todo get cat id and collect at index 6 and 7
            pass
        # todo

        index = 7
        # cat_id
        # todo category

        self.db_finance.insert(refs.tbl_fin_trans,
                               "transaction_by, date, type, category_id, amount, vendor_id, photo_id",
                               (self._job.chat_id, t_date, t_type, cat_id, value, vendor_id, self._job.photo_ids))
        self._job.complete()

        # todo add another option with the same params

    def finance_photo(self):
        if not os.path.exists(refs.finance_images):
            os.makedirs(refs.finance_images)

        for value in self._job.photo_ids:
            shutil.move(os.path.join(refs.telepot_image_dump, value),
                        os.path.join(refs.finance_images, value))

        # todo OCR
