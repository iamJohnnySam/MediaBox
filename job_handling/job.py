import json
import os

from PIL import Image

import global_var
from record import logger
from database_manager.sql_connector import sql_databases
from record.custom_exceptions import *


class Job:
    def __init__(self, telepot_account: str = global_var.main_telepot_account,
                 message: dict = None,
                 job_id: int = 0,
                 chat_id: int = 0, username: str = "", reply_to: int = 0, function: str = "",
                 collection=None):

        self._db = sql_databases[global_var.db_admin]
        self._telepot_account = telepot_account

        # Important Variables
        self._chat_id: int = chat_id
        self._reply_to: int = reply_to
        self._username: str = username
        self._function: str = function
        if collection is None:
            self._collection: [str] = []
        else:
            self._collection: [str] = collection
        self._photo_ids: [str] = []
        self._current_callback = 0

        manual_params = function != ""

        if message is None and job_id == 0 and not manual_params:
            logger.log(job_id=job_id, error_code=40001)
            raise InvalidParameterException("Not enough parameters to create a job")

        elif message is not None:
            self._job_id: int = 0
            self.breakdown_message(message)

        elif job_id != 0:
            self._job_id = job_id
            query = f"SELECT account, chat_id, reply_to, username, class, function, collection, photo " \
                    f"FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
            result = self._db.run_sql(query)
            if len(result) == 0:
                logger.log(job_id=job_id, error_code=40003)
                raise LookupError

            self._telepot_account: str = result[0]
            self._chat_id: int = int(result[1])
            self._reply_to: int = int(result[2]) if result[3] is not None else 0
            self._username: str = result[3] if result[3] is not None else "User"
            self._function: str = result[5] if result[5] is not None else ""
            self._collection: [str] = list(result[6].split(';')) if result[6] is not None else []
            self._photo_ids = result[7].split(";")

        elif manual_params:
            if chat_id == 0:
                (self._chat_id, self._username) = self.get_master_details()
            if self._username == "":
                self._username = "User"

        else:
            logger.log(job_id, error_code=40002)
            raise InvalidParameterException("Error creating job")

    def breakdown_message(self, msg: dict):
        self._chat_id = msg['chat']['id']
        self._reply_to = msg['message_id']
        self._username = msg['chat']['first_name']

        if 'photo' in msg.keys():
            for pic in msg['photo']:
                self._photo_ids.append(msg['photo'][pic]['file_id'])
            self.update_db('photo', self.photo_names, force=True)

        if 'text' in msg.keys():
            content = msg['text']

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

    # Job Properties
    @property
    def master(self):
        query = f"SELECT chat_id FROM {global_var.tbl_chats} WHERE master = 1"
        result = self._db.run_sql(query)[0]
        return result

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
    def collection(self) -> list:
        if self.is_stored:
            query = f"SELECT collection FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
            result = self._db.run_sql(query)
            collect = result[0].split(";")
        else:
            collect = self._collection
        return collect

    @collection.setter
    def collection(self, collect):
        self._collection = collect
        self.update_db('collection', collect)

    @property
    def photo_ids(self):
        return self._photo_ids

    @property
    def photo_names(self) -> [str]:
        names = []
        for pic in range(len(self._photo_ids)):
            names.append(f"{self._job_id}_{pic}.jpg")
        return names

    @property
    def photo_loc(self):
        """Returns the full path in which the photo is saved"""
        if not os.path.exists(global_var.telepot_image_dump):
            os.makedirs(global_var.telepot_image_dump)
        return [os.path.join(global_var.telepot_image_dump, x) for x in self.photo_names]

    @property
    def cb_id(self):
        """Returns the next available callback ID to use when generating a keyboard. Everytime this value is referred
        a new callback ID is generated."""
        self.store_message()
        query = f"SELECT cb_id FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
        cb = int(self._db.run_sql(query)[0])
        cb = cb + 1
        self.update_db('cb_id', str(cb), force=True)
        self._current_callback = cb
        return cb

    # Checks
    @property
    def is_authorised(self):
        if self._db.exists(global_var.tbl_chats, f"chat_id = '{self.chat_id}'") == 0:
            return False
        else:
            return True

    @property
    def is_master(self):
        return self.master == self.chat_id

    @property
    def is_stored(self):
        return self._job_id != 0

    @property
    def has_photo(self):
        return self._photo_ids != []

    # Functions
    def complete(self):
        if self.is_stored:
            self.update_db('complete', True)
            logger.log(job_id=self._job_id, msg="Message Completed")

    def update_db(self, field: str, item, force=False):
        if type(item) is list:
            item = ";".join([str(ele) for ele in item])

        if force and not self.is_stored:
            self.store_message()

        if self.is_stored:
            query = f"UPDATE {global_var.tbl_jobs} SET {field} = '{item}' WHERE job_id = '{str(self._job_id)}'"
            self._db.run_sql(query)

    def get_master_details(self) -> (int, str):
        query = f"SELECT chat_id, chat_name FROM {global_var.tbl_chats} WHERE master = 1"
        return self._db.run_sql(query)

    @property
    def replies(self):
        query = f"SELECT replies FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
        return json.loads(self._db.run_sql(query)[0])

    @property
    def callbacks(self):
        query = f"SELECT callbacks FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
        return json.loads(self._db.run_sql(query)[0])

    def store_message(self):
        if not self.is_stored:
            if self._function == "":
                logger.log(job_id=self.job_id, msg="Message to be stored without function", log_type="warn")

            self._job_id = self._db.insert(table=global_var.tbl_jobs,
                                           columns="account, chat_id, reply_to, username, function, collection",
                                           val=(self._telepot_account, self._chat_id, self._reply_to, self._username,
                                                self._function))
            self.update_db("collection", self._collection)
            self.update_db("photo", self._photo_ids)
            logger.log(job_id=self.job_id, msg="Message Stored")

    def store_photos(self):
        for pic in self.photo_loc:
            foo = Image.open(pic)
            w, h = foo.size
            if w > h and w > 1024:
                foo = foo.resize((1024, int(h * 1024 / w)))
            elif h > w and h > 1024:
                foo = foo.resize((int(w * 1024 / h), 1024))

            foo.save(pic, optimize=True, quality=95)
            logger.log(job_id=self.job_id, msg=f'Received Photo > {pic}, File size > {foo.size}')

    def collect(self, value: str, index: int):
        if self.is_stored:
            query = f"SELECT collection FROM {global_var.tbl_jobs} WHERE job_id ='{str(self._job_id)}'"
            self._collection = self._db.run_sql(query)[0].split(";")

        if index < len(self._collection):
            self._collection[index] = value
            logger.log(job_id=self.job_id, msg=f"({self._job_id}): Replaced with {value} at index {index}.")
        elif index == len(self._collection):
            self._collection.append(value)
            logger.log(job_id=self.job_id, msg=f"({self._job_id}): Added {value} at index {index}.")
        else:
            logger.log(job_id=self.job_id, error_code=40004)
            raise IndexError("Cannot collect")

        self.update_db("collection", self._collection)

    def add_reply(self, replies):
        d = self.replies
        d[str(self._current_callback)] = replies
        self.update_db('replies', json.dumps(d))

    def add_callback(self, cb: int, value):
        d = self.callbacks
        d[str(cb)] = value
        self.update_db('callbacks', json.dumps(d))
