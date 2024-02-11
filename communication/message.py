import json
import os
from datetime import datetime

from PIL import Image

import global_var
import logger
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import sql_databases


class Message:
    def __init__(self, message_handler=None, message=None, db_id=None):
        if (message_handler is None or message is None) and db_id is None:
            logger.log("Error Creating Message Object", message_type="error")
            return
        elif message_handler is None or message is None:
            # todo get from db
            pass
        else:
            self._message_handler = message_handler
            self._message: dict = message
            self._db_id = db_id

        self._value = ""
        self._function = ""
        self.admin_db = sql_databases[global_var.db_admin]

    @property
    def msg_id(self):
        if self._db_id is None:
            self.store_message()
        return self._db_id

    @property
    def telepot_account(self):
        return self._message_handler

    @property
    def chat_id(self):
        return self._message['chat']['id']

    @property
    def message_id(self):
        return self._message['message_id']

    @property
    def f_name(self):
        return str(self._message['chat']['first_name'])

    @property
    def content(self):
        try:
            return str(self._message['text'])
        except KeyError:
            logger.log('No Text Key: ' + str(self._message), message_type="error")
            return ""

    @property
    def first_word(self):
        return self.breakdown_content()

    @property
    def cb_id(self):
        query = f"SELECT cb_id FROM {global_var.tbl_messages} WHERE msg_id ='{str(self._db_id)}'"
        cb = int(self.admin_db.run_sql(query)[0])
        cb = cb + 1
        query = f"UPDATE {global_var.tbl_messages} SET cb_id = '{str(cb)}' WHERE msg_id = '{str(self._db_id)}'"
        self.admin_db.run_sql(query)
        return cb

    @property
    def function(self):
        return self._function

    @function.setter
    def function(self, func):
        self._function = func

    @property
    def value(self):
        if self._value == "":
            self.breakdown_content()
        return self._value

    @property
    def photo_id(self):
        if 'photo' in self._message.keys():
            return self._message['photo'][-1]['file_id']
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
    def check_sender(self):
        if self.admin_db.exists(global_var.tbl_chats, f"chat_id = '{self.chat_id}'") == 0:
            return False
        else:
            return True

    @property
    def collection(self):
        if self.stored_message:
            query = f"SELECT collection FROM {global_var.tbl_messages} WHERE msg_id ='{str(self._db_id)}'"
            result = self.admin_db.run_sql(query)
            collect = result[0]
        else:
            collect = None

        return collect

    @collection.setter
    def collection(self, collect):
        if self.stored_message:
            query = f"UPDATE {global_var.tbl_messages} SET collection = '{collect}' WHERE msg_id = '{str(self._db_id)}'"
            self.admin_db.run_sql(query)

    @property
    def stored_message(self):
        return self._db_id is not None

    @property
    def is_master(self):
        master = JSONEditor(global_var.telepot_accounts).read()[self.telepot_account]["master"]
        return master == self.chat_id

    @property
    def replies(self):
        query = f"SELECT replies FROM {global_var.tbl_messages} WHERE msg_id ='{str(self._db_id)}'"
        return json.loads(self.admin_db.run_sql(query)[0])

    @property
    def callbacks(self):
        query = f"SELECT callbacks FROM {global_var.tbl_messages} WHERE msg_id ='{str(self._db_id)}'"
        return json.loads(self.admin_db.run_sql(query)[0])

    def breakdown_content(self):
        f = self.content.split(" ")[0].lower()
        if f.startswith("/"):
            self._value = self.content.replace(f, "").strip()
        else:
            self._value = self.content
        logger.log(f"{str(self._message_handler)}\t{str(self.chat_id)} - {f}.")
        return f

    def store_message(self):
        if self._function == "":
            logger.log("Message to be stored without function", message_type="warn")
        self._db_id = self.admin_db.insert(table=global_var.tbl_messages,
                                           columns="account, message, function",
                                           val=(self._message_handler, json.dumps(self._message), self._function))
        logger.log(f"({self._db_id}): Message Stored")

    def complete(self):
        if self.stored_message:
            self.admin_db.run_sql(f"UPDATE {global_var.tbl_messages} SET complete = '1' "
                                  f"WHERE msg_id = '{str(self._db_id)}'")
            logger.log(f"({self._db_id}): Message Completed")

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
            except ValueError:\
                return False

        return True

    def collect(self, value: str, index: int):
        if not self.stored_message:
            self.store_message()
            collection = []
        else:
            collection = self.collection.split(";")

        if index < len(collection):
            collection[index] = value
            logger.log(f"({self._db_id}): Replaced with {value} at index {index}.")
        elif index == len(collection):
            collection.append(value)
            logger.log(f"({self._db_id}): Added {value} at index {index}.")
        else:
            logger.log(f"({self._db_id}): Cannot Collect {value} at index {index} on collection: {collection}.",
                       message_type="error")
            return False

        new_collect = ""
        for item in collection:
            new_collect = new_collect + ";" + item

        self.collection = new_collect

        return True

    def add_reply(self, cb: int, replies):
        d = self.replies
        d[str(cb)] = replies
        query = f"UPDATE {global_var.tbl_messages} SET replies = '{json.dumps(d)}' WHERE msg_id = '{str(self._db_id)}'"
        self.admin_db.run_sql(query)

    def add_callback(self, cb: int, value):
        d = self.callbacks
        d[str(cb)] = value
        query = f"UPDATE {global_var.tbl_messages} SET callbacks = '{json.dumps(d)}' WHERE msg_id = '{str(self._db_id)}'"
        self.admin_db.run_sql(query)
