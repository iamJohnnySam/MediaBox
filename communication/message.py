import os
from datetime import datetime

from PIL import Image

import global_var
import logger
from database_manager.sql_connector import sql_databases


class Message:
    database = "administration"
    database_chats = "telepot_allowed_chats"
    database_groups = "telepot_groups"
    database_msg = "telepot_messages"

    def __init__(self, tp_account: str, message: dict):
        self._function: str = ""
        self._value: str = ""
        self._command: str = ""
        self.message: dict = message
        self._telepot_account: str = tp_account

        self.filed: bool = False
        self._msg_id: int = 0
        self._cb_id: int = 0

        self.replies = {}

    @property
    def chat_id(self):
        return self.message['chat']['id']

    @property
    def telepot_account(self):
        return self._telepot_account

    @property
    def message_id(self):
        return self.message['message_id']

    @property
    def msg_id(self):
        return self._msg_id

    @property
    def cb_id(self):
        self._cb_id = self._cb_id + 1
        return self._cb_id

    @property
    def f_name(self):
        return str(self.message['chat']['first_name'])

    @property
    def text(self):
        try:
            return str(self.message['text'])
        except KeyError:
            logger.log('No Text Key: ' + str(self.message), message_type="error")
            return ""

    @property
    def photo_id(self):
        if 'photo' in self.message.keys():
            return self.message['photo'][-1]['file_id']
        else:
            return ""

    @property
    def photo_name(self):
        return f'{self.chat_id}-{self.message_id}-{datetime.now().strftime("%y%m%d%H%M%S")}.png'

    @property
    def photo_loc(self):
        if not os.path.exists(global_var.telepot_image_dump):
            os.makedirs(global_var.telepot_image_dump)
        return os.path.join(global_var.telepot_image_dump, self.photo_name)

    @property
    def command(self):
        if self._command == "":
            self.get_command_value()
        return self._command

    @property
    def value(self):
        if self._value == "":
            self.get_command_value()
        return self._value

    @property
    def function(self):
        return self._function

    @function.setter
    def function(self, func: str):
        self._function = func
        self.file()

    def check_sender(self):
        if sql_databases[self.database].exists(self.database_chats, f"chat_id = '{self.chat_id}'") == 0:
            return False
        else:
            return True

    def get_command_value(self):
        self._command = self.text.split(" ")[0].lower()
        if self._command.startswith("/"):
            self._value = self.text.replace(self._command, "").strip()
        else:
            self._value = self.text
        logger.log(str(self._telepot_account) + "\t" + str(self.chat_id) + " - " + str(self._command))

    def store_photo(self):
        foo = Image.open(self.photo_loc)
        w, h = foo.size
        if w > h and w > 1024:
            foo = foo.resize((1024, int(h * 1024 / w)))
        elif h > w and h > 1024:
            foo = foo.resize((int(w * 1024 / h), 1024))

        foo.save(self.photo_loc, optimize=True, quality=95)
        logger.log(f'Received Photo > {self.photo_name}, File size > {foo.size}')

    def check_value(self, index: int = 0, replace_str: str = "",
                    check_int: bool = False,
                    check_float: bool = False):
        try:
            val = self.value.split(" ")[index] if " " in self.value else self.value
        except IndexError:
            logger.log(f"{self.value} has no index {index}")
            return False

        if replace_str != "" and replace_str in val:
            val = val.replace(replace_str, "").strip()

        if val == "":
            return False

        if check_int:
            try:
                int(val)
            except ValueError:
                return False

        if check_float:
            try:
                float(val)
            except ValueError:
                return False

        return True

    def file(self):
        if not self.filed:
            cols = "account, chat_id, message_id, function, photo"

            func = None if self.function == "" else self.function
            photo_id = None if self.photo_id == "" else self.photo_id
            vals = (self._telepot_account, self.chat_id, self.message_id, func, photo_id)

            success, self._msg_id = sql_databases[self.database].insert(self.database_msg, cols, vals)
            logger.log(f"Filed Message: {self.msg_id}")

            self.filed = True

    def add_reply(self, reply_id):
        self.replies[] = reply_id
