import math

from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup

import passwords
from common_workspace import global_var
from shared_tools.message_tools import create_keyboard_data
from shared_models.job import Job
from shared_tools.logger import log

message_id = 0


class Message:
    def __init__(self, send_string: str,
                 job: Job = None,
                 keyboard=None,
                 get_input=False, index=0,
                 group: str = None,
                 photo: str = ""):

        self.send_string = send_string
        self.keyboard = keyboard
        self.group = group
        self.photo = photo
        self.get_input = get_input
        self.index = index
        self.no_message = False

        if job is None:
            global message_id
            message_id = message_id + 1
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
        if len(button_text) == 0 or len(button_text) != len(button_val):
            log(job_id=self.msg_id, error_code=20011)
            log(job_id=self.msg_id, msg="Button Text Length " + str(len(button_text)))
            log(job_id=self.msg_id, msg="Button Value Length " + str(len(button_val)))
            return

        buttons = []
        for i in range(len(button_text)):

            button_data = create_keyboard_data(msg_id=self.msg_id,
                                               reply_to=reply_to,
                                               function=function[i] if type(function) is list else function,
                                               button_text=button_text[i],
                                               button_value=button_val[i],
                                               collection=collection)

            buttons.append(InlineKeyboardButton(text=str(button_text[i]), callback_data=button_data))
            log(job_id=self.msg_id, msg=f'Keyboard button created > {button_data}')

        keyboard_markup = []
        c = 0
        for i in range(len(arrangement)):
            keyboard_row = []
            for j in range(arrangement[i]):
                keyboard_row.append(buttons[c])
                c = c + 1
            keyboard_markup.append(keyboard_row)
        self.keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)

    def keyboard_extractor(self, function, options, index=0, button_text=None, bpr: int = 3,
                           add_cancel: bool = False, add_other: bool = False, collection: list = None,
                           reply_to=None):

        if button_text is None:
            button_text = options

        if collection is None:
            collection = []

        if collection and type(collection) is list:
            collection_str = ";".join([str(ele) for ele in collection])
        else:
            collection_str = ""

        button_value = []
        for text in options:
            button_value.append(f'{index};{text}')

        if add_other:
            button_text.append("Other")
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

    def compress(self):
        return {
            "msg_id": self.msg_id,
            "channel": self._channel,
            "msg": self.send_string,
            "chat": self.chat_id,
            "reply": self.reply_to,
            "group": self.group,
            "keyboard": self.keyboard,
            "photo": self.photo
        }
