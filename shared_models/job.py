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

        self.generate_new_id()
        self.job_id = current_id

        self.function: str = function
        self.channel: str = channel
        self.chat_id: int = chat_id
        self.username: str = username
        self.reply_to: int = reply_to
        self.collection: list[str] = collection
        self.is_background_task = background_task

        self.called_back = False
        self.bypass_channel_check = False
        self.module = ""

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

    def generate_new_id(self):
        global current_id
        current_id = current_id + 1
        if current_id >= 10_000:
            current_id = 1
            log(job_id=current_id, msg="Job ID rolled over to 1")
        self.job_id = current_id

    def job_compress(self):
        log(self.job_id, f"Job ({self.function}) compressed with collection: {self.collection}")
        return {
            "id": self.job_id,
            "packet_type": "job",
            "channel": self.channel,
            "chat": self.chat_id,
            "username": self.username,
            "reply": self.reply_to,
            "function": self.function,
            "module": self.module,
            "collection": self.collection,
            "background_task": self.is_background_task
        }

    def job_decompress(self, job_details: dict):
        self.channel = job_details["channel"]
        self.chat_id = job_details["chat"]
        self.username = job_details["username"]
        self.reply_to = job_details["reply"]
        self.function = job_details["function"]
        self.module = job_details["module"]
        self.collection = job_details["collection"]
        self.is_background_task = job_details["background_task"]
        log(self.job_id, f"Job ({self.function}) decompressed with collection: {self.collection}")

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
