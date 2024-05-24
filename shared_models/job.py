import json

import telepot
from PIL import Image

import passwords
from common_workspace import global_var
from shared_tools.custom_exceptions import *
from shared_tools.logger import log

current_id = 0


class Job:
    def __init__(self, function: str, channel: str = "",
                 chat_id: int = 0, username: str = "", reply_to: int = 0,
                 collection=None,
                 background_task: bool = False):

        """
        :param function: Main function identifier.
        :param channel: Name of the telepot account which initiated request.
        :param chat_id: Chat ID who initiated request.
        :param username: Name of Chat who initiated the request.
        :param reply_to: Message ID that initiated the request.
        :param collection: Data collection for function.
        :param background_task: Block outgoing messages if true.
        """

        global current_id
        current_id = current_id + 1
        if current_id >= 10_000:
            log(msg="Job ID rolled over to 0")
            current_id = 1
        self.job_id = current_id

        self.function: str = function
        self.channel: str = channel
        self.chat_id: int = chat_id
        self.username: str = username
        self.reply_to: int = reply_to
        self.collection: list[str] = collection
        self.is_background_task = background_task
        self.called_back = False

        if self.function == "":
            log(job_id=self.job_id, error_code=40001)
            raise InvalidParameterException("Not enough parameters to create a job")

        if self.channel == "":
            self.channel = global_var.main_telegram_channel

        if chat_id == 0:
            self._chat_id = passwords.telegram_chat_id
            self.username = "Boss"

        if self.username == "":
            self.username = "User"

        if self.collection is None:
            self.collection: [str] = []

        if type(self.collection) is not list:
            log(self.job_id, error_code=40002)
            raise InvalidParameterException("Error creating job")

    def compress(self):
        log(self._job_id, f"Job ({self.function}) compressed with collection: {self.collection}")
        return {
            "job": self.job_id,
            "channel": self.channel,
            "chat": self.chat_id,
            "username": self.username,
            "reply": self.reply_to,
            "function": self.function,
            "collection": self.collection,
            "background_task": self.is_background_task
        }

    def decompress(self, job_details: dict):
        self.channel = job_details["channel"]
        self.chat_id = job_details["chat"]
        self.username = job_details["username"]
        self.reply_to = job_details["reply"]
        self.function = job_details["function"]
        self.collection = job_details["collection"]
        self.is_background_task = job_details["background_task"]
        log(self._job_id, f"Job ({self.function}) decompressed with collection: {self.collection}")

    def collect(self, value: str, index: int):
        if index < 0:
            index = 0

        if index < len(self.collection):
            self.collection[index] = value
            log(job_id=self.job_id, msg=f"Replaced with {value} at index {index}.")
        elif index == len(self.collection):
            self.collection.append(value)
            log(job_id=self.job_id, msg=f"Added {value} at index {index}.")
        else:
            log(job_id=self.job_id, error_code=40004)
            raise IndexError("Cannot collect")

    # Job Properties

    def store_message(self):
        if not self.is_stored:
            if self._function == "":
                log(job_id=self.job_id, msg="Message to be stored without function", log_type="warn")

            cols = "account, chat_id, reply_to, username, function"
            vals = (self._channel, self._chat_id, self._reply_to, self._username, self._function)

            self._job_id = self._db.insert(table=refs.tbl_jobs, columns=cols, val=vals)
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


