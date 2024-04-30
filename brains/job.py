import json
import os

import telepot
from PIL import Image

import refs
from database_manager.sql_connector import SQLConnector
from tools import params
from tools.custom_exceptions import *
from tools.logger import log


class Job:
    def __init__(self, telepot_account: str = "",
                 message: dict = None,
                 job_id: int = 0,
                 chat_id: int = 0, username: str = "", reply_to: int = 0, function: str = "",
                 collection=None,
                 background_task: bool = False):

        self._telepot_account = params.get_param('telepot',
                                                 'main_channel') if telepot_account == "" else telepot_account

        self._db = SQLConnector(0, database=refs.db_admin)

        self.is_background_task = background_task
        self.called_back = False

        # Important Variables
        self._job_id = job_id
        self._db.job_id = self._job_id
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

        self.user_input = ""
        self._collected = False
        self._replied = False
        self._waiting_to_get_job = False

        manual_params = function != ""

        if message is None and job_id == 0 and not manual_params:
            log(job_id=job_id, error_code=40001)
            raise InvalidParameterException("Not enough parameters to create a job")

        elif message is not None:
            self._job_id: int = 0
            self.breakdown_message(message)

        elif job_id != 0:
            self._job_id = job_id
            self._db.job_id = self._job_id
            self._get_job()

        elif manual_params:
            if chat_id == 0:
                (self._chat_id, self._username) = self.get_master_details()
            if self._username == "":
                self._username = "User"

        else:
            log(job_id, error_code=40002)
            raise InvalidParameterException("Error creating job")

        self.reply_log: dict = {}

    def _get_job(self):
        columns = "account, chat_id, reply_to, username, function, collection, photo, replies, cb_id"
        result = self._db.select(table=refs.tbl_jobs,
                                 columns=columns,
                                 where={"job_id": self._job_id})
        if len(result) == 0:
            log(job_id=self._job_id, error_code=40003)
            raise LookupError

        self._telepot_account: str = result[0]
        self._chat_id: int = int(result[1])
        self._reply_to: int = int(result[2]) if result[3] is not None else 0
        self._username: str = result[3] if result[3] is not None else "User"
        self._function: str = result[4] if result[4] is not None else ""
        self._collection: [str] = list(result[5].split(';')) if result[5] is not None else []
        self._photo_ids = [] if result[6] is None else result[6].split(";")
        self.reply_log = {} if result[7] is None else json.loads(result[7])
        self._current_callback = int(result[8])

        log(self._job_id, f"Job ({self._function}) recovered from job_id with collection: {self._collection}")

    def update_job(self):
        if self.is_stored:
            result = self._db.select(refs.tbl_jobs, "replies, cb_id", {"job_id": self._job_id})
            if len(result) == 0:
                log(job_id=self._job_id, error_code=40003)
                raise LookupError

            self.reply_log = {} if result[0] is None else json.loads(result[0])
            self._current_callback = int(result[1])

            log(self._job_id, f"Job ({self._function}) recovered from job_id with collection: {self._collection}")

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
            self.user_input = content

            first_word: str = content.split(" ")[0].lower()
            if first_word.startswith("/"):
                self._function = first_word.replace("/", "")

                if self._function == "start":
                    self._function = "help"

                value = content.replace(first_word, "").strip()
                self._collection = value.split(" ")
                self._collected = True

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

        log(job_id=self._job_id, msg=f"Function: {self._function}, Value: {value}")

    # Job Properties
    @property
    def master(self):
        result = self._db.select(refs.tbl_chats, "chat_id", {"master": 1})[0]
        return result

    @property
    def job_id(self) -> int:
        return self._job_id

    @job_id.setter
    def job_id(self, in_job_id):
        self._job_id = in_job_id
        self._get_job()
        self._db.job_id = self._job_id

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
        if self.is_stored and self._collection == []:
            result = self._db.select(table=refs.tbl_jobs,
                                     columns="collection",
                                     where={"job_id": self._job_id})
            collect = result[0].split(";")
        else:
            collect = self._collection
        return collect

    @collection.setter
    def collection(self, collect: list):
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
        if not os.path.exists(refs.telepot_image_dump):
            os.makedirs(refs.telepot_image_dump)
        return [os.path.join(refs.telepot_image_dump, x) for x in self.photo_names]

    @property
    def cb_id(self):
        """Returns the next available callback ID to use when generating a keyboard. Everytime this value is referred
                a new callback ID is generated."""
        if not self.is_stored:
            log(self.job_id, error_code=40006)
            self.store_message()

        self._current_callback = self._current_callback + 1
        return self._current_callback

    # Checks
    @property
    def is_authorised(self):
        if self._db.check_exists(refs.tbl_chats, {"chat_id": self.chat_id}) == 0:
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
            self.store_message()
            self.update_db('complete', item=True)
            log(job_id=self._job_id, msg="Message Completed")

    def update_db(self, field: str, item: str | bool | list | int | float, force=False):
        if type(item) is str and ";" in item:
            raise InvalidParameterException

        if type(item) is list:
            item = ";".join([str(ele) for ele in item])

        if force and not self.is_stored:
            self.store_message()

        if self.is_stored:
            self._db.update(table=refs.tbl_jobs,
                            update={field: item, "cb_id": self._current_callback},
                            where={'job_id': self._job_id})

    def get_master_details(self) -> (int, str):
        return self._db.select(table=refs.tbl_chats,
                               columns="chat_id, chat_name",
                               where={"master": 1})

    @property
    def replies(self):
        if self.reply_log == {} and self.is_stored:
            reps = self._db.select(table=refs.tbl_jobs, columns="replies", where={"job_id": self._job_id})[0]
            if reps is None:
                return {}
            else:
                return json.loads(reps)
        else:
            return self.reply_log

    @property
    def callbacks(self):
        return json.loads(self._db.select(table=refs.tbl_jobs, columns="callbacks", where={"job_id": self._job_id})[0])

    def store_message(self):
        if not self.is_stored:
            if self._function == "":
                log(job_id=self.job_id, msg="Message to be stored without function", log_type="warn")

            self._job_id = self._db.insert(table=refs.tbl_jobs,
                                           columns="account, chat_id, reply_to, username, function",
                                           val=(self._telepot_account, self._chat_id, self._reply_to,
                                                self._username,
                                                self._function))
            self._db.job_id = self._job_id

            if self._photo_ids:
                self.update_db("photo", self._photo_ids)

        if self._replied:
            self.update_db('replies', json.dumps(self.reply_log))
            self._replied = False

        if self._collected:
            self.update_db("collection", self._collection)
            self._collected = False

        log(job_id=self.job_id, msg="Message Stored")

    def store_photos(self):
        for pic in self.photo_loc:
            foo = Image.open(pic)
            w, h = foo.size
            if w > h and w > 1024:
                foo = foo.resize((1024, int(h * 1024 / w)))
            elif h > w and h > 1024:
                foo = foo.resize((int(w * 1024 / h), 1024))

            foo.save(pic, optimize=True, quality=95)
            log(job_id=self.job_id, msg=f'Received Photo > {pic}, File size > {foo.size}')

    def collect(self, value: str, index: int):
        if self.is_stored and self._collection == []:
            result = self._db.select(table=refs.tbl_jobs, columns="collection", where={"job_id": self._job_id})[0]
            self._collection = [] if result is None else result.split(";")

        if index < 0:
            index = 0

        if index < len(self._collection):
            self._collection[index] = value
            log(job_id=self.job_id, msg=f"Replaced with {value} at index {index}.")
        elif index == len(self._collection):
            self._collection.append(value)
            log(job_id=self.job_id, msg=f"Added {value} at index {index}.")
        else:
            log(job_id=self.job_id, error_code=40004)
            raise IndexError("Cannot collect")

        # self.update_db("collection", self._collection)
        self._collected = True

    def add_reply(self, replies):
        if self.is_stored:
            self.store_message()
            d = self.replies
            if not type(d) == dict:
                log(job_id=self.job_id, error_code=40007, msg=f'Type = {type(d)}, value = {d}')
            else:
                self.reply_log = d

        for reply in replies:
            if "reply_markup" not in reply.keys():
                _ = self.cb_id
            self.reply_log[self._current_callback] = telepot.message_identifier(reply)
            log(job_id=self.job_id, msg=f"Added reply with callback: {self._current_callback}.")

        self.update_db('replies', json.dumps(self.reply_log))
        self._replied = True

    def add_callback(self, cb: int, value):
        d = self.callbacks
        d[str(cb)] = value
        self.update_db('callbacks', json.dumps(d))
