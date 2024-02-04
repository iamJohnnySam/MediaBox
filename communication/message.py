import os
from datetime import datetime

from PIL import Image

import global_var
import logger
from database_manager.sql_connector import sql_databases


class Message:
    database_allowed_chats = "telepot_allowed_chats"
    database_groups = "telepot_groups"

    def __init__(self, tp_account, message):
        self._value: str = ""
        self._command: str = ""
        self.message = message
        self.telepot_account = tp_account

    @property
    def chat_id(self):
        return self.message['chat']['id']

    @property
    def message_id(self):
        return self.message['message_id']

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
        return self.message['photo'][-1]['file_id']

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

    def check_sender(self):
        if sql_databases["administration"].exists(self.database_allowed_chats, f"chat_id = '{self.chat_id}'") == 0:
            return False
        else:
            return True

    def get_command_value(self):
        self._command = self.text.split(" ")[0].lower()
        if self._command.startswith("/"):
            self._value = self.text.replace(self._command, "").strip()
        else:
            self._value = self.text
        logger.log(str(self.telepot_account) + "\t" + str(self.chat_id) + " - " + str(self._command))

    def store_photo(self):
        foo = Image.open(self.photo_loc)
        w, h = foo.size
        if w > h and w > 1024:
            foo = foo.resize((1024, int(h * 1024 / w)))
        elif h > w and h > 1024:
            foo = foo.resize((int(w * 1024 / h), 1024))

        foo.save(self.photo_loc, optimize=True, quality=95)
        logger.log(f'Received Photo > {self.photo_name}, File size > {foo.size}')
