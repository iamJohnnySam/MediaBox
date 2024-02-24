import json
import os
from datetime import datetime

from PIL import Image

import global_var
import logger
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import sql_databases
from exceptions.custom_exceptions import *


class Job:
    def __init__(self, telepot_account: str = global_var.main_telepot_account,
                 message: dict = None,
                 job_id: int = 0):

        self._db = sql_databases[global_var.db_admin]
        self._telepot_account = telepot_account
        self._master = JSONEditor(global_var.telepot_accounts).read()[self.telepot_account]["master"]

        # Important Variables
        # todo link them to parameters when done
        self._chat_id = None
        self._reply_to = None
        self._username = None
        self._function = None
        self._collection = []

        # todo check other params
        manual_params = False

        if message is None and job_id == 0 and not manual_params:
            raise InvalidParameterException("Not enough parameters to create a job")

        elif message is not None and job_id == 0 and not manual_params:
            self._job_id: int = 0
            self.breakdown_message(message)

        elif message is None and job_id != 0 and not manual_params:
            query = f"SELECT account, message, function FROM {global_var.tbl_jobs} " \
                    f"WHERE job_id ='{str(self._job_id)}'"
            result = self._db.run_sql(query)
            if len(result) == 0:
                raise LookupError
            self._telepot_account, self._message, self._function = int(result[0])

        elif message is None and job_id == 0 and manual_params:
            # todo

            # todo get username from sql
            pass

        else:
            raise InvalidParameterException("Error creating job")

    def breakdown_message(self, msg: dict):
        self._chat_id = msg['chat']['id']
        self._reply_to = msg['message_id']
        self._username = msg['chat']['first_name']

        if 'text' in msg.keys():
            content = self._message['text']

            first_word: str = content.split(" ")[0].lower()
            if first_word.startswith("/"):
                self._function = first_word.replace("/", "")
                value = content.replace(first_word, "").strip()
                self._collection = value.split(" ")

            else:
                words = len(content.split(" "))
                if first_word in ['cancel'] and words == 1:
                    self._function = 'cancel'
                elif first_word in ['help', 'hi', 'hello'] and words == 1:
                    self._function = 'help'
                else:
                    self._function = "chat"
                value = content
                self._collection = [value]

        else:
            self._function = "no_function"
            value = ""
            self._collection = []

        logger.log(job_id=self._job_id, msg=f"Function: {self._function}, Value: {value}")

    def breakdown_callback(self):
        # todo
        pass

    # Job Properties
    @property
    def job_id(self) -> int:
        return self._job_id

    @property
    def telepot_account(self):
        return self._telepot_account

    @property
    def chat_id(self) -> int:
        return self._chat_id

    @property
    def message_id(self) -> int:
        return self._reply_to

    @property
    def f_name(self) -> str:
        return self._username

    @property
    def function(self):
        return self._function

    @function.setter
    def function(self, func):
        self._function = func
        self.update_db('function', self._function)

    @property
    def photo_id(self):
        """Returns the photo ID of the initial message and automatically stores the message on the database"""
        if 'photo' in self._message.keys():
            self.update_db('photo', self.photo_name, force=True)
            return self._message['photo'][-1]['file_id']
        else:
            return ""

    @property
    def photo_name(self):
        """Returns the photo name associated with this message"""
        return f'{self._job_id}.png'

    @property
    def photo_loc(self):
        """Returns the full path in which the photo is saved"""
        if not os.path.exists(global_var.telepot_image_dump):
            os.makedirs(global_var.telepot_image_dump)
        return os.path.join(global_var.telepot_image_dump, self.photo_name)

    # Checks
    @property
    def is_authorised(self):
        if self._db.exists(global_var.tbl_chats, f"chat_id = '{self.chat_id}'") == 0:
            return False
        else:
            return True

    @property
    def is_master(self):
        return self._master == self.chat_id

    @property
    def is_stored(self):
        return self._job_id != 0




    # Functions
    def complete(self):
        if self.is_stored:
            self.update_db('complete', True)
            logger.log(job_id=self._job_id, msg="Message Completed")


    def update_db(self, field: str, item, force=False):
        if force and not self.stored_message:
            self.store_message()

        if self.stored_message:
            query = f"UPDATE {global_var.tbl_jobs} SET {field} = '{item}' WHERE job_id = '{str(self._job_id)}'"
            self._db.run_sql(query)



















    @property
    def cb_id(self):
        """Returns the next available callback ID to use when generating a keyboard. Everytime this value is referred
        a new callback ID is generated."""
        query = f"SELECT cb_id FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
        cb = int(self._db.run_sql(query)[0])
        cb = cb + 1
        self.update_db('cb_id', str(cb), force=True)
        return cb




    @property
    def first_value(self):
        """Returns the first value of the content"""
        return self.value.split(" ")[0] if " " in self.value else self.value

    @property
    def collection(self) -> list:
        if self.stored_message:
            query = f"SELECT collection FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
            result = self._db.run_sql(query)
            collect = result[0].split(";")
        else:
            collect = []

        return collect

    @collection.setter
    def collection(self, collect):
        self.update_db('collection', collect, force=True)

    @property
    def replies(self):
        query = f"SELECT replies FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
        return json.loads(self._db.run_sql(query)[0])

    @property
    def callbacks(self):
        query = f"SELECT callbacks FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
        return json.loads(self._db.run_sql(query)[0])

    def store_message(self):
        if self._function == "":
            logger.log("Message to be stored without function", log_type="warn")
        self._job_id = self._db.insert(table=global_var.tbl_jobs,
                                       columns="account, message, function",
                                       val=(self._telepot_account, json.dumps(self._message), self._function))
        logger.log(f"({self._job_id}): Message Stored")



    def store_photo(self):
        foo = Image.open(self.photo_loc)
        w, h = foo.size
        if w > h and w > 1024:
            foo = foo.resize((1024, int(h * 1024 / w)))
        elif h > w and h > 1024:
            foo = foo.resize((int(w * 1024 / h), 1024))

        foo.save(self.photo_loc, optimize=True, quality=95)
        logger.log(f'Received Photo > {self.photo_name}, File size > {foo.size}')

    def collect(self, value: str, index: int):
        if not self.stored_message:
            self.store_message()
            collection = []
        else:
            collection = self.collection

        if index < len(collection):
            collection[index] = value
            logger.log(f"({self._job_id}): Replaced with {value} at index {index}.")
        elif index == len(collection):
            collection.append(value)
            logger.log(f"({self._job_id}): Added {value} at index {index}.")
        else:
            logger.log(f"({self._job_id}): Cannot Collect {value} at index {index} on collection: {collection}.",
                       log_type="error")
            return False

        new_collect = ""
        for item in collection:
            new_collect = new_collect + ";" + item

        self.collection = new_collect

        return True

    def add_reply(self, cb: int, replies):
        d = self.replies
        d[str(cb)] = replies
        self.update_db('replies', json.dumps(d))

    def add_callback(self, cb: int, value):
        d = self.callbacks
        d[str(cb)] = value
        self.update_db('callbacks', json.dumps(d))
        self._called_back = True
