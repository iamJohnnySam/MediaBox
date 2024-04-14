import math
import os
from datetime import datetime

from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup

import refs
from database_manager.json_editor import JSONEditor
from brains.job import Job
from database_manager.sql_connector import SQLConnector
from tools import logger
from tools.custom_exceptions import InvalidParameterException


class Message:
    def __init__(self, send_string: str, job: Job = None, chat=None, reply_to=None,
                 keyboard=None,
                 group: str = None,
                 photo: str = ""):

        if job is not None:
            self._job_id = job.job_id
        else:
            self._job_id = 0

        self._db = SQLConnector(self._job_id, database=refs.db_admin)

        self.send_string = send_string
        self.job = job
        self._chat = chat
        self._reply_to = reply_to
        self.keyboard = keyboard
        self.group = group
        self.photo = photo
        self._this_telepot_account = ""

        # Check Message
        if self.send_string == "" or self.send_string is None:
            logger.log(job_id=self.job_id, error_code=20006)
            self.send_string = "NO MESSAGE"

    @property
    def job_id(self):
        if self._job_id != 0:
            return self._job_id
        else:
            if self.job is not None:
                return self.job.job_id
            else:
                return 0

    @property
    def master(self):
        result = self._db.select(table=refs.tbl_chats, columns="chat_id", where={"master": 1})[0]
        return result

    @property
    def chats(self):
        if self.job is None and self._chat is None and self.group is None:
            chats = [self.master]

        elif self.group is not None:
            if self._db.check_exists(refs.tbl_groups, {"group_name": self.group}) == 0:
                logger.log(job_id=self.job_id, error_code=20007)
                raise ValueError
            result = self._db.select(table=refs.tbl_groups, columns="chat_id", where={"group_name": self.group},
                                     fetch_all=True)
            chats = [row[0] for row in result]

        elif self.job is not None:
            chats = [self.job.chat_id]

        elif self._chat is not None and type(self._chat) == int:
            chats = [self._chat]

        else:
            logger.log(job_id=self.job_id, error_code=20008)
            raise InvalidParameterException

        return chats

    @property
    def reply_to(self):
        if self.group is None and self._reply_to is None and self.job is not None:
            if self._this_telepot_account == "" or self.job.telepot_account == self._this_telepot_account:
                self._reply_to = self.job.message_id
            else:
                self._reply_to = None
                logger.log(job_id=self.job_id, error_code=20009)
        elif self.group is not None and self._reply_to is not None:
            logger.log(job_id=self.job_id, error_code=20010)
            self._reply_to = None
        if self._reply_to == 0:
            self._reply_to = None
        return self._reply_to

    @property
    def this_telepot_account(self):
        return self._this_telepot_account

    @this_telepot_account.setter
    def this_telepot_account(self, account):
        self._this_telepot_account = account

    def add_job_keyboard(self, button_text: list, button_val: list, arrangement: list):
        cb_id = self.job.cb_id
        if self.job_id == 0:
            self._job_id = self.job.job_id

        self._arrange_keyboard(self.job_id, button_text, button_val, arrangement, cb_id)

    def _add_one_time_keyboard(self, button_text: list, button_val: list, arrangement: list):
        job_id = datetime.now().strftime("%Y%m%d%H%M%S")
        cb_id = "/"
        self._arrange_keyboard(job_id, button_text, button_val, arrangement, cb_id)

    def _arrange_keyboard(self, job_id, button_text: list, button_val: list, arrangement: list, cb_id):
        if len(button_text) == 0 or len(button_text) != len(button_val):
            logger.log(job_id=self.job_id, error_code=20011)
            logger.log(job_id=self.job_id, msg="Button Text Length " + str(len(button_text)))
            logger.log(job_id=self.job_id, msg="Button Value Length " + str(len(button_val)))
            return

        buttons = []
        for i in range(len(button_text)):
            # FORMAT = job_id; cb_id; btn_text; (step; value)
            button_prefix = f"{str(job_id)};{str(cb_id)};{button_text[i]}"
            button_data = f"{button_prefix};{button_val[i]}"

            if len(button_data) >= 60:
                telepot_cb = {button_prefix: button_data}
                save_loc = os.path.join(refs.loc_telepot_callback, f"{str(job_id)}_cb.json")
                JSONEditor(save_loc).add_level1(telepot_cb, job_id=self.job_id)
                button_data = f"{button_prefix};X"

            buttons.append(InlineKeyboardButton(text=str(button_text[i]), callback_data=button_data))
            logger.log(job_id=self.job_id, msg=f'Keyboard button created > {button_data}')

        keyboard_markup = []
        c = 0
        for i in range(len(arrangement)):
            keyboard_row = []
            for j in range(arrangement[i]):
                keyboard_row.append(buttons[c])
                c = c + 1
            keyboard_markup.append(keyboard_row)
        self.keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)

    def job_keyboard_extractor(self, index, options, bpr: int = 3, add_cancel: bool = False, add_other: bool = False):
        button_text = options

        button_value = []
        for text in button_text:
            button_value.append(f'{index};{text}')

        if add_other:
            button_text.append("Other")
            button_value.append(f'{index};{"/GET"}')

        arrangement = [bpr for _ in range(int(math.floor(len(button_text) / bpr)))]
        if len(button_text) % bpr != 0:
            arrangement.append(len(button_text) % bpr)

        if add_cancel:
            button_text.append("Cancel")
            button_value.append(f'{index};/CANCEL')
            arrangement.append(1)

        logger.log(job_id=self.job.job_id, msg="Keyboard extracted > " + str(arrangement))

        self.add_job_keyboard(button_text, button_value, arrangement)

    def function_keyboard_extractor(self, function, options: list[str], button_text=None, bpr: int = 3,
                                    add_cancel: bool = False, add_other: bool = False):
        if button_text is None:
            button_text = []

        if not button_text:
            button_text = options

        button_value = []

        for i in range(len(options)):
            if type(function) == list:
                f = function[i]
            else:
                f = function
            button_value.append(f'{f};{options[i]}')

        if add_other and type(function) == str:
            button_text.append("Other")
            button_value.append(f'{function};{"/GET"}')

        arrangement = [bpr for _ in range(int(math.floor(len(button_text) / bpr)))]
        if len(button_text) % bpr != 0:
            arrangement.append(len(button_text) % bpr)

        if add_cancel:
            button_text.append("Cancel")
            button_value.append(f'cancel;/CANCEL')
            arrangement.append(1)

        logger.log(job_id=self.job.job_id, msg="Keyboard extracted > " + str(arrangement))

        self._add_one_time_keyboard(button_text, button_value, arrangement)

    def send_to_master(self):
        self.job = None
        self._chat = None
        self.group = None
