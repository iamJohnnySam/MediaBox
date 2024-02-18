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
    def __init__(self, message_handler: str = global_var.main_telepot_account,
                 message: dict = None,
                 job_id: int = 0):

        self.admin_db = sql_databases[global_var.db_admin]

        # todo check other params
        manual_params = False

        if message is None and job_id == 0 and not manual_params:
            raise InvalidParameterException("Not enough parameters to create a job")

        elif message is not None and job_id == 0 and not manual_params:
            self._job_id: int = 0
            self.breakdown_message()

        elif message is None and job_id != 0 and not manual_params:
            query = f"SELECT account, message, function FROM {global_var.tbl_jobs} " \
                    f"WHERE job_id ='{str(self._job_id)}'"
            result = self.admin_db.run_sql(query)
            if len(result) == 0:
                raise LookupError
            self._message_handler, self._message, self._function = int(result[0])

        elif message is None and job_id == 0 and manual_params:
            # todo
            pass

        else:
            raise ImpossibleException("Error creating job")

        self._value = ""
        self._called_back = False

    def breakdown_message(self):
        pass

    @property
    def job_id(self) -> int:
        """Returns the Job ID if message is stored on the database. Else it will store it and return Job ID"""
        if self._job_id is None:
            self.store_message()
        return self._job_id

    @property
    def telepot_account(self):
        """Returns the telepot account name from which the initial message originated"""
        return self._message_handler

    @property
    def chat_id(self) -> int:
        """Returns the chat ID of the initial message"""
        return self._message['chat']['id']

    @property
    def message_id(self) -> int:
        """Returns the message ID of the initial message"""
        return self._message['message_id']

    @property
    def f_name(self) -> str:
        """Returns the first name of the person who sent the initial message"""
        return str(self._message['chat']['first_name'])

    @property
    def content(self):
        """Returns the raw content of the initial message."""
        try:
            return str(self._message['text'])
        except KeyError:
            logger.log('No Text Key: ' + str(self._message), log_type="warn")
            return ""

    @property
    def first_word(self):
        """Returns the first word of the content. Used to find the command"""
        return self.breakdown_content()

    @property
    def called_back(self):
        """Returns True if the message was called back. Returns False if the message is a new message."""
        return self._called_back

    @property
    def cb_id(self):
        """Returns the next available callback ID to use when generating a keyboard. Everytime this value is referred
        a new callback ID is generated."""
        query = f"SELECT cb_id FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
        cb = int(self.admin_db.run_sql(query)[0])
        cb = cb + 1
        self.update_db('cb_id', str(cb), force=True)
        return cb

    @property
    def function(self):
        """Returns the set function of the message. If function is not set, a blank string is returned"""
        return self._function

    @function.setter
    def function(self, func):
        """Use to set the function for the message"""
        self._function = func
        if self.stored_message:
            self.update_db('function', self._function)

    @property
    def value(self):
        if self._value == "":
            self.breakdown_content()
        return self._value

    @property
    def first_value(self):
        """Returns the first value of the content"""
        return self.value.split(" ")[0] if " " in self.value else self.value

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
        return f'{self.chat_id}-{self.message_id}-{self.generated_time}.png'

    @property
    def photo_loc(self):
        """Returns the full path in which the photo is saved"""
        if not os.path.exists(global_var.telepot_image_dump):
            os.makedirs(global_var.telepot_image_dump)
        return os.path.join(global_var.telepot_image_dump, self.photo_name)

    @property
    def check_sender(self):
        """Returns True if the sender is an authorized sender"""
        if self.admin_db.exists(global_var.tbl_chats, f"chat_id = '{self.chat_id}'") == 0:
            return False
        else:
            return True

    @property
    def collection(self) -> list:
        if self.stored_message:
            query = f"SELECT collection FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
            result = self.admin_db.run_sql(query)
            collect = result[0].split(";")
        else:
            collect = []

        return collect

    @collection.setter
    def collection(self, collect):
        self.update_db('collection', collect, force=True)

    @property
    def stored_message(self):
        return self._job_id is not None

    @property
    def is_master(self):
        master = JSONEditor(global_var.telepot_accounts).read()[self.telepot_account]["master"]
        return master == self.chat_id

    @property
    def replies(self):
        query = f"SELECT replies FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
        return json.loads(self.admin_db.run_sql(query)[0])

    @property
    def callbacks(self):
        query = f"SELECT callbacks FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
        return json.loads(self.admin_db.run_sql(query)[0])

    def breakdown_content(self):
        """Breaks down the content of the initial message and returns the first word while saving the value. If the
        first word started with '/' then the value will be taken from the second word onward. If not the entire message
        will be taken as the value."""
        f = self.content.split(" ")[0].lower()
        if f.startswith("/"):
            self._value = self.content.replace(f, "").strip()
        else:
            self._value = self.content
        logger.log(f"{str(self._message_handler)}\t{str(self.chat_id)} - {f}.")
        return f

    def store_message(self):
        if self._function == "":
            logger.log("Message to be stored without function", log_type="warn")
        self._job_id = self.admin_db.insert(table=global_var.tbl_jobs,
                                            columns="account, message, function",
                                            val=(self._message_handler, json.dumps(self._message), self._function))
        logger.log(f"({self._job_id}): Message Stored")

    def update_db(self, field: str, item, force=False):
        if force and not self.stored_message:
            self.store_message()

        if self.stored_message:
            query = f"UPDATE {global_var.tbl_jobs} SET {field} = '{item}' WHERE job_id = '{str(self._job_id)}'"
            self.admin_db.run_sql(query)

    def complete(self):
        if self.stored_message:
            self.update_db('complete', True)
            logger.log(f"({self._job_id}): Message Completed")

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
