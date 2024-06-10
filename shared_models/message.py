import math

import passwords
from common_workspace import global_var
from shared_models.job import Job
from shared_tools.logger import log

message_id = 0


class Message:
    def __init__(self, send_string: str,
                 job: Job = None,
                 get_input=False, index=0,
                 group: str = None,
                 photo: str = ""):

        self.send_string = send_string
        self.keyboard = False
        self.keyboard_details = {}
        self.group = group
        self.photo = photo
        self.get_input = get_input
        self.index = index
        self.no_message = False
        self._job = job
        self._compressed_job = {} if self.job is None else self.job.job_compress()

        if job is None:
            global message_id
            message_id = message_id + 1
            if message_id == 1000:
                message_id = 1
            self.msg_id = f"m{message_id}"
            self.chat_id = passwords.telegram_chat_id
            self.reply_to = None
            self._channel = global_var.main_telegram_channel
        else:
            self.msg_id = job.job_id
            self.chat_id = job.chat_id
            self.reply_to = job.reply_to
            self._channel = job.channel
            self.no_message = job.is_background_task

        if self.group is not None:
            self.reply_to = None
            log(job_id=self.msg_id, error_code=20010)

        if self.send_string == "" or self.send_string is None:
            log(job_id=self.msg_id, error_code=20006)
            self.send_string = "- NO MESSAGE -"

    @property
    def channel(self):
        return self._channel

    @property
    def job(self):
        return self._job

    @job.setter
    def job(self, j: Job):
        self._job = j
        self._compressed_job = j.job_compress()

    @channel.setter
    def channel(self, val):
        if val != self._channel:
            log(job_id=self.msg_id, error_code=20009)
            self.reply_to = None
            self._channel = val

    @property
    def master(self):
        return passwords.telegram_chat_id

    def add_keyboard(self, function: str | list[str], reply_to, button_text: list, button_val: list, arrangement: list,
                     collection: str):
        self.keyboard = True
        self.keyboard_details["function"] = function
        self.keyboard_details["reply_to"] = reply_to
        self.keyboard_details["button_text"] = button_text
        self.keyboard_details["button_val"] = button_val
        self.keyboard_details["arrangement"] = arrangement
        self.keyboard_details["collection"] = collection

    def keyboard_extractor(self, function, options, index=0, button_text=None, bpr: int = 3,
                           add_cancel: bool = False, add_other: bool = False, collection: list = None,
                           reply_to=None):

        if button_text is None:
            button_text = options

        if collection is None:
            collection = []

        if collection and type(collection) is list:
            collection_str = ";".join([str(ele) for ele in collection])
            log(job_id=message_id, msg=f"Collection String: {collection_str}")
        else:
            collection_str = ""
            log(job_id=message_id, msg=f"Collection not found")

        button_value = []
        for text in options:
            button_value.append(f'{index};{text}')

        if add_other:
            button_text.append("#Other")
            button_value.append(f'{index};/GET')

        arrangement = [bpr for _ in range(int(math.floor(len(button_text) / bpr)))]
        if len(button_text) % bpr != 0:
            arrangement.append(len(button_text) % bpr)

        if add_cancel:
            button_text.append("Cancel")
            button_value.append(f'{index};/CANCEL')
            arrangement.append(1)

        log(job_id=self.msg_id, msg="Keyboard extracted > " + str(arrangement))

        self.add_keyboard(function=function, reply_to=reply_to,
                          button_text=button_text, button_val=button_value, arrangement=arrangement,
                          collection=collection_str)

    def send_to_master(self):
        self._channel = global_var.main_telegram_channel
        self.chat_id = passwords.telegram_chat_id
        self.reply_to = None
        self.group = None

    def message_compress(self):
        log(self.msg_id, f"Message ({self.send_string}) compressed.")
        return {
            "id": self.msg_id,
            "packet_type": "message",
            "channel": self._channel,
            "msg": self.send_string,
            "chat": self.chat_id,
            "reply": self.reply_to,
            "group": self.group,
            "keyboard": self.keyboard_details,
            "photo": self.photo,
            "get_input": self.get_input,
            "no_message": self.no_message,
            "index": self.index,
            "job": self._compressed_job,
            "collection": self.job.collection
        }

    def message_decompress(self, message_details: dict):
        self._channel = message_details["channel"]
        self.send_string = message_details["msg"]
        self.chat_id = message_details["chat"]
        self.reply_to = message_details["reply"]
        self.group = message_details["group"]
        self.keyboard_details = message_details["keyboard"]
        self.keyboard = False if self.keyboard_details == {} else True
        self.photo = message_details["photo"]
        self.get_input = message_details["get_input"]
        self.no_message = message_details["no_message"]
        self.index = message_details["index"]
        self._compressed_job = message_details["job"]
        log(self.msg_id, f"Message ({self.send_string}) decompressed.")
