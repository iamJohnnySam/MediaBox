import os

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup

import global_var
from logging import logger
from module.job import Job
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import sql_databases
from tasker import task_queue


class Messenger:

    def __init__(self, telepot_account: str, telepot_key: str, telepot_master: int):
        self.telepot_account = telepot_account
        self.master = telepot_master

        # Waiting user input
        self.waiting_user_input = {}

        # Get Commands
        self.commands = JSONEditor(global_var.telepot_commands).read()

        # Listen
        self.bot = telepot.Bot(telepot_key)
        MessageLoop(self.bot, {'chat': self.handle,
                               'callback_query': self.handle_callback}).run_as_thread()
        logger.log(job_id=0, msg=f'Telepot {telepot_account} listening')

    def handle(self, msg):
        message = Job(self.telepot_account, msg)

        if not message.is_authorised():
            self.bot.sendMessage(message.chat_id, "Hello " + message.f_name + "! You're not allowed to be here")
            string = f"Unauthorised Chat access: {message.f_name}, chat_id: {message.chat_id}"
            self.send_now(string)
            logger.log(job_id=message.job_id, msg=string, log_type="warn")
            message.complete()
            return

        if 'photo' in msg.keys():
            self.handle_photo(message)

        if 'text' in msg.keys():
            self.handle_text(message)
        else:
            logger.log(job_id=message.job_id, msg="Unknown Chat type", log_type="error")

    def handle_photo(self, msg: Job):
        try:
            self.bot.download_file(msg.photo_id, msg.photo_loc)
        except PermissionError:
            logger.log(job_id=msg.job_id, msg="Permission Error")
            self.send_now("PERMISSION ERROR")

    def handle_text(self, msg: Job):
        if msg.function == "no_function":
            task_queue.add_job(msg)
            logger.log(job_id=msg.job_id, msg="No function call detected")

        elif msg.function == "cancel":
            # todo cancel procedure. Remove from waiting list and trigger fail command
            pass

        elif msg.function in self.commands.keys():
            if type(self.commands[msg.function]) is bool:
                self.send_now("That's not a command", job=msg)
                logger.log(job_id=msg.job_id, msg="Invalid command", log_type="warn")
                msg.complete()
                return
            elif self.telepot_account != "main" and self.telepot_account not in self.commands[msg.function].keys():
                self.send_now("That command does not work on this chatbot", job=msg)
                logger.log(job_id=msg.job_id, msg="Invalid command for chatbot", log_type="warn")
                msg.complete()
                return
            task_queue.add_job(msg)

        elif msg.function == "chat":
            if msg.chat_id in self.waiting_user_input:
                # todo
                self.received_user_input(msg)

            else:
                self.send_now("Chatbot Disabled. Type /help to find more information", job=msg)

        else:
            self.send_now("Sorry, that command is not known to me...", job=msg)

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

    def send_now(self, send_string: str, job: Job = None, chat=None, reply_to=None,
                 keyboard=None,
                 group: str = None,
                 image: bool = False, photo: str = ""):

        # Check Message
        if send_string == "" or send_string is None:
            logger.log("No message", log_type="error")
            return

        # Check Chat ID
        if job is None and chat is None and group is None:
            chats = [self.master]
        elif group is not None:
            if sql_databases[global_var.db_admin].exists(global_var.tbl_groups, f"group_name = '{group}'") == 0:
                logger.log("Group does not exist", log_type="error")
                return
            query = f"SELECT chat_id FROM {global_var.tbl_groups} WHERE group_name = '{group}'"
            result = sql_databases["administration"].run_sql(query, fetch_all=True)
            chats = [row[0] for row in result]
        elif job is not None and chat is None:
            chats = [job.chat_id]
        else:
            logger.log("Chat ID conditions are not met correctly", log_type="error")
            return

        # Check Reply to
        if group is None and reply_to is None and job is not None:
            if job.telepot_account == self.telepot_account:
                reply_to = job.message_id
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

        replies = self.send_now(send_string=send_string, job=msg, keyboard=keyboard,
                                group=group, image=image, photo=photo)

        msg.add_reply(cb_id, replies)

    def get_value_from_user(self, msg: Job, inquiry="value"):
        # todo get value
        pass
