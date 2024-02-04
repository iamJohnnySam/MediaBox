import inspect
import math
import os
from datetime import datetime

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup

import global_var
import logger
from communication.message import Message
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import sql_databases


class CommunicatorBase:
    database_groups = "telepot_groups"

    def __init__(self, telepot_account):
        self.telepot_account = telepot_account

        # Waiting user input
        self.waiting_user_input = {}
        self.messages = {}

        # Set up Telepot Account
        telepot_accounts = JSONEditor(global_var.telepot_accounts).read()
        self.bot = telepot.Bot(telepot_accounts[telepot_account]["account"])
        self.master = telepot_accounts[telepot_account]["master"]

        # Get Commands
        self.command_dictionary = JSONEditor(f'{global_var.telepot_commands}telepot_commands_'
                                             f'{self.telepot_account}.json').read()

        # Listen
        MessageLoop(self.bot, {'chat': self.handle,
                               'callback_query': self.handle_callback}).run_as_thread()
        logger.log('Telepot ' + telepot_account + ' listening')

    def send_now(self, send_string: str, msg: Message = None, chat=None, reply_to=None,
                 keyboard=None,
                 group: str = None,
                 image: bool = False, photo: str = ""):

        if send_string == "" or send_string is None:
            logger.log("NO MESSAGE", message_type="error")
            return

        if msg is None and chat is None and group is None:
            chats = [self.master]

        elif group is not None:
            exists = sql_databases["administration"].exists(self.database_groups, f"group_name = '{group}'") == 0
            if exists:
                logger.log("Group does not exist", message_type="error")
                return

            result = sql_databases["administration"].run_sql(
                f"SELECT chat_id FROM {self.database_groups} WHERE group_name = '{group}'",
                fetch_all=True)
            chats = [row[0] for row in result]

        elif msg is not None and chat is None:
            chats = [msg.chat_id]

        else:
            return

        if group is None and reply_to is None and msg is not None:
            if msg.telepot_account == self.telepot_account:
                reply_to = msg.msg_id

        replies = []
        for chat in chats:
            if image:
                message = self.bot.sendPhoto(chat,
                                             photo=open(str(photo), 'rb'),
                                             reply_to_message_id=reply_to,
                                             caption=send_string,
                                             reply_markup=keyboard)
                replies.append(message)
            else:
                message = self.bot.sendMessage(chat, str(send_string),
                                               reply_to_message_id=reply_to,
                                               reply_markup=keyboard)
                replies.append(message)

            logger.log(str(chat) + " - " + str(message['message_id']) + " - Message: " + str(send_string))

        if len(replies) == 1:
            return replies[0]
        else:
            return replies

    def link_msg_to_buttons(self, message, buttons):
        for button in buttons:
            button_dict = {button: message}
            JSONEditor(global_var.telepot_callback_database +
                       self.callback_id_prefix + 'telepot_button_link.json').add_level1(button_dict)

    def manage_chat_group(self, group, chat_id, add=True, remove=False):
        message_type = "info"
        where = f"chat_id = '{chat_id}' AND group_name = '{group}';"
        if not add ^ remove:
            msg = "Invalid command"
            message_type = "error"
        elif add and sql_databases["administration"].exists(self.database_groups, where) == 0:
            cols = "chat_id, group_name"
            vals = (chat_id, group)
            sql_databases["administration"].insert(self.database_groups, cols, vals)
            msg = f"Added {chat_id} to {group} group"
        elif remove and sql_databases["administration"].exists(self.database_groups, where) != 0:
            sql_databases["administration"].run_sql(f"DELETE FROM {self.database_groups} WHERE " + where)
            msg = f"Removed {chat_id} from {group} group"
        else:
            msg = "Nothing to do"

        logger.log(msg, message_type)
        return msg

    def handle(self, msg):
        message = Message(self.telepot_account, msg)

        if message.check_sender():
            if 'text' in msg.keys():
                self.handle_text(message)
            elif 'photo' in msg.keys():
                self.handle_photo(message)
            else:
                logger.log("Unknown Chat type", message_type="error")
        else:
            self.bot.sendMessage(message.chat_id, "Hello " + message.f_name + "! You're not allowed to be here")
            self.send_now(f"Unauthorised Chat access: {message.f_name}, chat_id: {message.chat_id}")
            logger.log(f"Unauthorised Chat access: {message.f_name}, chat_id: {message.chat_id}",
                       message_type="warn")

    def handle_text(self, msg):
        if msg.command in self.command_dictionary.keys():
            function = self.command_dictionary[msg.command]["function"]
            msg.function = function
            logger.log(str(msg.chat_id) + ' - Calling Function: ' + function)
            func = getattr(self, function)
            func(msg)

        elif msg.command == "/alive":
            self.send_now(f"{str(msg.chat_id)}\nHello{msg.f_name}! I'm Alive and kicking!",
                          chat=msg.chat_id,
                          reply_to=msg.message_id)

        elif msg.command == "/time":
            self.send_now(str(datetime.now()), chat=msg.chat_id, reply_to=msg.message_id)

        elif msg.command == "/start_over" or msg.command == "/exit_all" or msg.command == "/reboot_pi":
            if msg.chat_id == self.master:
                global_var.stop_all = True
                global_var.stop_cctv = True

                if msg.command == "/start_over":
                    global_var.restart = True
                elif msg.command == "/reboot_pi":
                    global_var.reboot_pi = True

                self.send_now("Completing ongoing tasks. Please wait.")

            else:
                self.send_now("This is a server command. Requesting admin...", chat=msg.chat_id,
                              reply_to=msg.message_id)
                self.send_now(f"{msg.command} requested by {msg.f_name}.")

        elif msg.command in ['/help', 'help', '/start', 'start', 'hi', 'hello']:
            message = "--- AVAILABLE COMMANDS ---"
            for command in self.command_dictionary.keys():
                if command.startswith('/'):
                    message = message + "\n" + command + " - " + self.command_dictionary[command]["definition"]
                else:
                    message = message + "\n\n" + command

            self.send_now(message, chat=msg.chat_id)

        elif msg.command.startswith("/"):
            self.send_now("Sorry, that command is not known to me...", chat=msg.chat_id)

        elif msg.chat_id in self.waiting_user_input:
            self.received_user_input(msg)

        else:
            self.send_now("Chatbot Disabled. Type /help to find more information", chat=msg.chat_id)

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

        button_text, button_cb, button_value, arrangement = self.keyboard_extractor(msg.photo_name, None,
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

    def handle_callback(self, query):
        try:
            msg_id = int(str(query['data']).split(",")[0])
        except ValueError:
            logger.log("Value error in callback " + str(query), message_type="error")
            return

        if msg_id == 0:
            pass

        query_id, from_id, query_data = telepot.glance(query, flavor='callback_query')
        logger.log('Callback Query: ' + " " + str(query_id) + " " + str(from_id) + " " + str(query_data))

        if str(from_id) in self.waiting_user_input.keys():
            logger.log("Unable to continue. Waiting user input.")
            return

        callback_id = str(query_data).split(",")[0]
        command = str(query_data).split(",")[1]

        if command == "X":
            comm = callback_id.split("_")[0] + "_" + callback_id.split("_")[1] + "_"
            telepot_callbacks = JSONEditor(global_var.telepot_callback_database
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
        message = JSONEditor(global_var.telepot_callback_database
                             + comm + 'telepot_button_link.json').read()[button_id]
        logger.log("Buttons to remove from message id " + str(message['message_id']))
        message_id = telepot.message_identifier(message)
        self.bot.editMessageReplyMarkup(message_id, reply_markup=keyboard)
        return message['message_id']

    def send_with_keyboard(self, send_string: str, msg: Message,
                           button_text: list, button_cb: list, button_val: list, arrangement: list,
                           group: str = None,
                           image: bool = False, photo: str = ""):

        if button_text is None or button_cb is None or button_val is None or arrangement is None:
            logger.log("Incomplete Buttons", message_type="error")
            return

        if len(button_text) == 0 or len(button_text) != len(button_cb) or len(button_text) != len(button_val):
            logger.log("Keyboard Generation error: " + str(send_string), message_type="error")
            logger.log("Button Text Length " + str(len(button_text)), message_type="error")
            logger.log("Button CB Length " + str(len(button_cb)), message_type="error")
            logger.log("Button Value Length " + str(len(button_val)), message_type="error")
            return

        button_ids = []
        buttons = []
        for i in range(len(button_text)):
            # FORMAT = msg_id, cb_id, btn_text, cb_function, value
            button_prefix = f"{str(msg.msg_id)},{str(msg.cb_id)},{button_text[i]}"
            button_data = f"{button_prefix},{button_cb[i].lower()},{button_val[i]}"

            if len(button_data) >= 60:
                telepot_cb = {button_prefix: button_data}
                save_loc = os.path.join(global_var.telepot_callback_database, f"{str(msg.msg_id)}_cb.json")
                JSONEditor(save_loc).add_level1(telepot_cb)
                button_data = f"{button_prefix},X"

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

    def keyboard_extractor(self, identifier, num, result, cb, bpr=3, sql_result=True, command_only=False):
        if sql_result:
            button_text = [row[0] for row in result]
        else:
            button_text = result
        button_cb = [cb] * len(button_text)
        button_value = []
        for text in button_text:
            if command_only:
                button_value.append(f'{identifier};{text}')
            else:
                button_value.append(f'{identifier};{num};{text}')
        arrangement = [bpr for _ in range(int(math.floor(len(button_text) / 3)))]
        if len(button_text) % bpr != 0:
            arrangement.append(len(button_text) % 3)
        logger.log("Keyboard extracted > " + str(arrangement))

        return button_text, button_cb, button_value, arrangement

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
