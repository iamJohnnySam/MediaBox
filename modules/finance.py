import os
import re
from datetime import datetime

import global_variables
import refs
from brains.job import Job
from database_manager.sql_connector import sql_databases
from modules.base_module import Module
from tools.custom_exceptions import InvalidParameterException
from tools.logger import log


# todo

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
        success, date = self.check_value(index=index, description="transaction date",
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



        try:
            amount = float(msg.value)
        except ValueError:
            self.send_now("Please type the amount in numbers only", chat=msg.chat_id, reply_to=msg.message_id)
            self.get_user_input(msg.chat_id, "finance", None)
            return

        if user_input and identifier is not None:
            sql_id = identifier
            query = f'UPDATE transaction_lkr SET amount = "{amount}" WHERE transaction_id = "{sql_id}"'
            sql_databases["finance"].run_sql(query)

        else:
            columns = 'transaction_by, amount'
            val = (msg.chat_id, amount)
            success, sql_id = self.db_finance.insert('transaction_lkr', columns, val,
                                                     get_id=True,
                                                     id_column='transaction_id')

        prefix = str(sql_id) + ";"

        self.send_with_keyboard(job=f'[{sql_id}] Is LKR {msg.value} an income or expense?',
                                chat_id=msg.chat_id,
                                button_text=["Income", "Expense", "Invest", "Delete"],
                                button_cb=["finance", "finance", "finance", "finance"],
                                button_val=[prefix + "1;income",
                                            prefix + "1;expense",
                                            prefix + "1;invest",
                                            prefix + "1;delete"],
                                arrangement=[3, 1],
                                reply_to=msg.message_id
                                )

    def finance_photo(self, callback_id, query_id, from_id, value):
        message_id = self.update_in_line_buttons(callback_id)
        self.bot.answerCallbackQuery(query_id, text='Got it')

        if not os.path.exists(global_var.finance_images):
            os.makedirs(global_var.finance_images)

        columns = 'transaction_by, photo_id'
        val = (from_id, value)
        success, sql_id = sql_databases["finance"].insert('transaction_lkr', columns, val,
                                                          get_id=True,
                                                          id_column='transaction_id')
        shutil.move(os.path.join(global_var.telepot_image_dump, value),
                    os.path.join(global_var.finance_images, value))
        self.send_now("How much is the amount?", chat=from_id, reply_to=str(message_id))
        self.get_user_input(from_id, "finance", sql_id)

    def cb_finance(self, callback_id, query_id, from_id, value):
        message_id = self.update_in_line_buttons(callback_id)
        self.bot.answerCallbackQuery(query_id, text='Got it')

        data = value.split(";")
        if data[2].lower() == "delete":
            query = f'DELETE FROM transaction_lkr WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query, fetch_all=True)
            return

        if data[1] == "1":
            query = f'UPDATE transaction_lkr SET type = "{data[2]}" WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query)

            d = datetime.now().strftime("%Y-%m-%d")
            query = f'UPDATE transaction_lkr SET date = "{d}" WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query)

            if data[2] == "invest":
                in_out = "income"
            else:
                in_out = data[2]

            query = f'SELECT DISTINCT type FROM categories WHERE in_out = "{in_out}"'
            result = list(sql_databases["finance"].run_sql(query, fetch_all=True))

            button_text, button_cb, button_value, arrangement = self.job_keyboard_extractor(data[0], "2", result,
                                                                                            'finance')
            button_text.append("Delete")
            button_cb.append("finance")
            button_value.append(f'{data[0]};2;Delete')
            arrangement.append(1)

            self.send_with_keyboard(job=f'[{data[0]}] What type of {data[2]} was it?',
                                    chat_id=from_id,
                                    button_text=button_text,
                                    button_cb=button_cb,
                                    button_val=button_value,
                                    arrangement=arrangement,
                                    reply_to=message_id
                                    )
        elif data[1] == "2":
            query = f'SELECT DISTINCT category FROM categories WHERE type = "{data[2]}"'
            result = list(sql_databases["finance"].run_sql(query, fetch_all=True))

            button_text, button_cb, button_value, arrangement = self.job_keyboard_extractor(data[0], "3", result,
                                                                                            'finance')
            button_text.append("Delete")
            button_cb.append("finance")
            button_value.append(f'{data[0]};3;Delete')
            arrangement.append(1)

            self.send_with_keyboard(job=f'[{data[0]}] What is the category of {data[2]}',
                                    chat_id=from_id,
                                    button_text=button_text,
                                    button_cb=button_cb,
                                    button_val=button_value,
                                    arrangement=arrangement,
                                    reply_to=message_id
                                    )
        elif data[1] == "3":
            query = f'SELECT category_id FROM categories WHERE category = "{data[2]}"'
            cat_id = list(sql_databases["finance"].run_sql(query))[0]
            query = f'UPDATE transaction_lkr SET category_id = "{cat_id}" WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query, fetch_all=True)
            log(f'Updated Transaction - {data[0]}')
            self.send_now(f'[{data[0]}] Transaction successfully updated', chat=from_id)

# todo add another option with the same params
