import os
from queue import Queue

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup

import global_var
import logger
from module.job import Job
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import sql_databases


class MessageHandler:

    def __init__(self, telepot_account: str, task_q: Queue):
        self.telepot_account = telepot_account
        self.task_q = task_q

        # Waiting user input
        self.waiting_user_input = {}

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

    def handle(self, msg):
        message = Job(self.telepot_account, msg)

        if not message.check_sender():
            self.bot.sendMessage(message.chat_id, "Hello " + message.f_name + "! You're not allowed to be here")
            string = f"Unauthorised Chat access: {message.f_name}, chat_id: {message.chat_id}"
            self.send_now(string)
            logger.log(string, log_type="warn")
            return

        if 'photo' in msg.keys():
            self.handle_photo(message)

        if 'text' in msg.keys():
            self.handle_text(message)
        else:
            logger.log("Unknown Chat type", log_type="error")

    def handle_photo(self, msg):
        try:
            self.bot.download_file(msg.photo_id, msg.photo_loc)
        except PermissionError:
            logger.log("Permission Error")
            self.send_now("PERMISSION ERROR")

    def handle_text(self, msg):
        if msg.content == "":
            msg.function = "no_function"
            self.task_q.put(msg)

        elif msg.first_word in self.command_dictionary.keys():
            function = self.command_dictionary[msg.first_word]["function"]
            msg.function = function
            self.task_q.put(msg)

        elif msg.first_word in ['/alive', '/time', '/start_over', '/exit_all', '/reboot_pi']:
            msg.function = msg.first_word.replace("/", "").strip()
            self.task_q.put(msg)

        elif msg.first_word in ['/cancel', 'cancel']:
            # todo cancel procedure. Remove from waiting list and trigger fail command
            pass

        elif msg.first_word in ['/help', 'help', '/start', 'start', 'hi', 'hello']:
            message = "--- AVAILABLE COMMANDS ---"
            for command in self.command_dictionary.keys():
                if command.startswith('/'):
                    message = message + "\n" + command + " - " + self.command_dictionary[command]["definition"]
                else:
                    message = message + "\n\n" + command
            self.send_now(message, chat=msg.chat_id)

        elif msg.first_word.startswith("/"):
            self.send_now("Sorry, that command is not known to me...", chat=msg.chat_id)

        elif msg.chat_id in self.waiting_user_input:
            self.received_user_input(msg)

        else:
            self.send_now("Chatbot Disabled. Type /help to find more information", chat=msg.chat_id)

    def handle_callback(self, query):
        try:
            q = str(query['data']).split(";")
        except ValueError:
            logger.log("Value error in callback " + str(query), log_type="error")
            return

        logger.log('Callback Query: ' + str(query['data']))

        if q[3] == "X":
            save_loc = os.path.join(global_var.telepot_callback_database, f"{q[0]}_cb.json")
            query = JSONEditor(save_loc).read()[f'{q[0]};{q[1]};{q[2]}']
            logger.log("Recovered Query: " + query)

        try:
            q = str(query['data']).split(";")
            msg_id = int(q[0])
        except ValueError:
            logger.log("Value error in callback " + str(query), log_type="error")
            return

        try:
            msg = Job(job_id=msg_id)
        except LookupError:
            logger.log("Message not found", log_type="error")
            # todo reply to callback as fail
            return

        self.task_q.put(msg)

    def send_now(self, send_string: str, msg: Job = None, chat=None, reply_to=None,
                 keyboard=None,
                 group: str = None,
                 image: bool = False, photo: str = ""):

        # Check Message
        if send_string == "" or send_string is None:
            logger.log("No message", log_type="error")
            return

        # Check Chat ID
        if msg is None and chat is None and group is None:
            chats = [self.master]
        elif group is not None:
            if sql_databases[global_var.db_admin].exists(global_var.tbl_groups, f"group_name = '{group}'") == 0:
                logger.log("Group does not exist", log_type="error")
                return
            query = f"SELECT chat_id FROM {global_var.tbl_groups} WHERE group_name = '{group}'"
            result = sql_databases["administration"].run_sql(query, fetch_all=True)
            chats = [row[0] for row in result]
        elif msg is not None and chat is None:
            chats = [msg.chat_id]
        else:
            logger.log("Chat ID conditions are not met correctly", log_type="error")
            return

        # Check Reply to
        if group is None and reply_to is None and msg is not None:
            if msg.telepot_account == self.telepot_account:
                reply_to = msg.message_id
            else:
                logger.log("Telepot account not matching.", log_type="error")
        elif group is not None and reply_to is not None:
            logger.log("Unable to reply for a group message. Reply reference will be removed.", log_type="warn")
            reply_to = None

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

        return replies

    def send_with_keyboard(self, send_string: str, msg: Job,
                           button_text: list, button_val: list, arrangement: list,
                           group: str = None,
                           image: bool = False, photo: str = ""):

        if len(button_text) == 0 or len(button_text) != len(button_val):
            logger.log("Keyboard Generation error: " + str(send_string), log_type="error")
            logger.log("Button Text Length " + str(len(button_text)), log_type="error")
            logger.log("Button Value Length " + str(len(button_val)), log_type="error")
            return

        buttons = []
        cb_id = msg.cb_id

        for i in range(len(button_text)):
            # FORMAT = msg_id; cb_id; btn_text; (step; value)
            button_prefix = f"{str(msg.job_id)};{str(cb_id)};{button_text[i]}"
            button_data = f"{button_prefix};{button_val[i]}"

            if len(button_data) >= 60:
                telepot_cb = {button_prefix: button_data}
                save_loc = os.path.join(global_var.telepot_callback_database, f"{str(msg.job_id)}_cb.json")
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

        replies = self.send_now(send_string=send_string, msg=msg, keyboard=keyboard,
                                group=group, image=image, photo=photo)

        msg.add_reply(cb_id, replies)

    def get_value_from_user(self, msg: Job, inquiry="value"):
        # todo get value
        pass
