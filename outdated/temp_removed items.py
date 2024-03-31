def link_msg_to_buttons(self, message, buttons):
    for button in buttons:
        button_dict = {button: message}
        JSONEditor(global_variables.telepot_callback_database +
                   self.callback_id_prefix + 'telepot_button_link.json').add_level1(button_dict)





def handle_photo(self, msg):
    try:
        self.bot.download_file(msg.photo_id, msg.photo_loc)
    except PermissionError:
        logger.log("Permission Error")
        self.send_now("PERMISSION ERROR")

    button_text = ["save_photo"]
    for key in self.command_dictionary.keys():
        if type(self.command_dictionary[key]) is dict and "photo" in self.command_dictionary[key].keys():
            button_text.append(f'{self.command_dictionary[key]["function"]}_photo')

    button_text, button_cb, button_value, arrangement = self.job_keyboard_extractor(msg.photo_name, None,
                                                                                    button_text,
                                                                                'run_command',
                                                                                    sql_result=False,
                                                                                    command_only=True)
    self.send_with_keyboard(msg="Which function to call?",
                            chat_id=msg.chat_id,
                            button_text=button_text,
                            button_cb=button_cb,
                            button_val=button_value,
                            arrangement=arrangement,
                            reply_to=msg.message_id
                            )


def quick_cb(self, query: dict, command: str, value: str):
    reply_to = query['inline_message_id']
    chat = query['from']['id']

    if command == "echo":
        self.send_now(send_string=value, reply_to=reply_to, chat=chat)

    elif command == "torrent":
        success, torrent_id = transmission.download(value)
        if success:

            self.send_now("Movie will be added to queue", reply_to=reply_to, chat=chat)

    elif command == "cancel":
        self.bot.editMessageReplyMarkup(reply_to, reply_markup=None)

    self.bot.answerCallbackQuery(query['id'], text='Handled')


def todo(self):
    # todo

    query_id, from_id, query_data = telepot.glance(query, flavor='callback_query')

    if str(from_id) in self.waiting_user_input.keys():
        logger.log("Unable to continue. Waiting user input.")
        return

    callback_id = str(query_data).split(",")[0]
    command = str(query_data).split(",")[1]

    if command == "X":
        comm = callback_id.split("_")[0] + "_" + callback_id.split("_")[1] + "_"
        telepot_callbacks = JSONEditor(global_variables.telepot_callback_database
                                       + comm + 'telepot_callback_database.json').read()

        query_data = telepot_callbacks[callback_id]
        logger.log("Recovered Query: " + query_data)

        command = str(query_data).split(",")[0]
        value = str(query_data).split(",")[1]

    else:
        value = str(query_data).split(",")[2]

    try:
        logger.log("Calling function: cb_" + command)
        func = getattr(self, "cb_" + command)
        func(callback_id, query_id, from_id, value)
    except (ValueError, SyntaxError) as error:
        self.bot.answerCallbackQuery(query_id, text='Unhandled')
        logger.log("Unhandled Callback: " + str(error), message_type="error")


def update_in_line_buttons(self, button_id, keyboard=None):
    comm = button_id.split("_")[0] + "_" + button_id.split("_")[1] + "_"
    message = JSONEditor(global_variables.telepot_callback_database
                         + comm + 'telepot_button_link.json').read()[button_id]
    logger.log("Buttons to remove from message id " + str(message['message_id']))
    message_id = telepot.message_identifier(message)
    self.bot.editMessageReplyMarkup(message_id, reply_markup=keyboard)
    return message['message_id']


def send_with_keyboard(self, send_string: str, msg: Message,
                       button_text: list, button_val: list, arrangement: list,
                       group: str = None,
                       image: bool = False, photo: str = ""):
    if len(button_text) == 0 or len(button_text) != len(button_val):
        logger.log("Keyboard Generation error: " + str(send_string), message_type="error")
        logger.log("Button Text Length " + str(len(button_text)), message_type="error")
        logger.log("Button Value Length " + str(len(button_val)), message_type="error")
        return

    button_ids = []
    buttons = []
    for i in range(len(button_text)):

        button_prefix = f"{str(msg.msg_id)};{str(msg.cb_id)};{button_text[i]}"
        button_data = f"{button_prefix};{button_val[i]}"

        if len(button_data) >= 60:
            telepot_cb = {button_prefix: button_data}
            save_loc = os.path.join(global_variables.telepot_callback_database, f"{str(msg.msg_id)}_cb.json")
            JSONEditor(save_loc).add_level1(telepot_cb)
            button_data = f"{button_prefix};X"

        buttons.append(InlineKeyboardButton(text=str(button_text[i]), callback_data=button_data))
        logger.log(f'Keyboard button created > {button_data}')

    keyboard_markup = []
    c = 0
    for i in range(len(arrangement)):
        keyboard_row = []
        for j in range(arrangement[i]):
            keyboard_row.append(buttons[c])
            c = c + 1
        keyboard_markup.append(keyboard_row)
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)

    message = self.send_now(send_string=send_string, msg=msg, keyboard=keyboard,
                            group=group, image=image, photo=photo)

    self.link_msg_to_buttons(message, button_ids)


def get_user_input(self, user_id, callback, argument):
    self.waiting_user_input[user_id] = {"callback": callback,
                                        "argument": argument}


def received_user_input(self, msg):
    cb = self.waiting_user_input[msg.chat_id]["callback"]
    arg = self.waiting_user_input[msg.chat_id]["argument"]
    del self.waiting_user_input[msg.chat_id]

    message = str(msg['text'])

    logger.log(f'Calling function: {cb} with arguments {arg} and {message}.')
    func = getattr(self, cb)
    if "cb_" in cb:
        func(None, msg.message_id, msg.chat_id, message)
    else:
        func(msg, user_input=True, identifier=arg)


def check_command_value(self, msg: Message, index: int = 0, replace: str = "", inquiry: str = "",
                        check_int: bool = False,
                        check_float: bool = False):
    current_frame = inspect.currentframe()
    call_frame = inspect.getouterframes(current_frame, 2)

    if msg.check_value(index=index, replace_str=replace, check_int=check_int, check_float=check_float):
        return True
    else:
        if inquiry != "":
            send_string = f'Please send the {inquiry}.'
        elif replace != "":
            send_string = f'Please send the amount in {replace}.'
        else:
            send_string = f'Please send the value.'

        self.send_now(send_string, chat=msg.chat_id, reply_to=msg.message_id)
        self.get_user_input(msg.chat_id, call_frame[1][3], None)
        return False

    # MAIN FUNCTIONS


def save_photo(self, callback_id, query_id, from_id, value):
    message_id = self.update_in_line_buttons(callback_id)
    self.bot.answerCallbackQuery(query_id, text='Image will be saved')

    logger.log("Image saved as " + value)
    self.send_now("Image saved as " + value,
                  image=False,
                  chat=from_id,
                  reply_to=message_id)


def cb_cancel(self, callback_id, query_id, from_id, value):
    self.update_in_line_buttons(callback_id)
    self.bot.answerCallbackQuery(query_id, text='Canceled')


def cb_echo(self, callback_id, query_id, from_id, value):
    self.send_now(value, chat=from_id)
    self.bot.answerCallbackQuery(query_id, text='Sent')


def cb_run_command(self, callback_id, query_id, from_id, value):
    result = value.split(';')
    logger.log("Calling function: " + result[1])
    func = getattr(self, result[1])
    func(callback_id, query_id, from_id, result[0])


if 'steps' in self.command_dictionary[msg.command].keys():
    msg.steps = self.command_dictionary[msg.command]['steps']
if 'database' in self.command_dictionary[msg.command].keys():
    msg.database = self.command_dictionary[msg.command]['database']

import os
from datetime import datetime

from PIL import Image

import global_variables
import logger
from database_manager.sql_connector import sql_databases


class Message:
    tp_db =
    tp_chats =
    tp_groups = "telepot_groups"
    tp_msg =

    def __init__(self, tp_account: str, message: dict):
        self._database: dict = {}
        self._steps: dict = {}
        self._function: str = ""
        self._value: str = ""
        self._command: str = ""
        self._message: dict = message
        self._telepot_account: str = tp_account

        self.filed: bool = False
        self._msg_id: int = 0
        self._cb_id: int = 0

        self.replies = {}

    @property
    def msg_id(self):
        return self._msg_id

    @property
    def cb_id(self):
        self._cb_id = self._cb_id + 1
        return self._cb_id

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

    @property
    def steps(self):
        return self._steps

    @steps.setter
    def steps(self, step: dict):
        self._steps = step

    @property
    def database(self):
        return self._database

    @database.setter
    def database(self, db: dict):
        self._database = db

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

            success, self._msg_id = sql_databases[self.tp_db].insert(self.tp_msg, cols, vals)
            logger.log(f"Filed Message: {self.msg_id}")

            self.filed = True

    def add_reply(self, reply_id):
        self.replies[] = reply_id
