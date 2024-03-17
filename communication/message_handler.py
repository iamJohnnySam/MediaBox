import os

import telepot
from telepot.loop import MessageLoop

from refs import db_telepot_commands, loc_telepot_callback, main_channel
from communication.message import Message
from tools import logger
from brains.job import Job
from database_manager.json_editor import JSONEditor
from brains import task_queue


class Messenger:

    def __init__(self, telepot_account: str, telepot_key: str, telepot_master: int):
        self.channel = telepot_account
        self.master = telepot_master

        # Waiting user input
        self.waiting_user_input = {}

        # Get Commands
        self.commands = JSONEditor(db_telepot_commands).read()

        # Listen
        self.bot = telepot.Bot(telepot_key)
        MessageLoop(self.bot, {'chat': self.handle,
                               'callback_query': self.handle_callback}).run_as_thread()
        logger.log(msg=f'Telepot {telepot_account} listening')

    def handle(self, msg):
        try:
            content = msg['text']
        except ValueError:
            content = "### No Message ###"
        logger.log(msg=f"INCOMING: {msg['chat']['id']}, Message: {content}", log_type="info")
        message = Job(self.channel, msg)

        if not message.is_authorised:
            self.bot.sendMessage(message.chat_id, "Hello " + message.f_name + "! You're not allowed to be here")
            string = f"Unauthorised Chat access: {message.f_name}, chat_id: {message.chat_id}"
            self.send_now(Message(string))
            logger.log(job_id=message.job_id, msg=string, log_type="warn")
            message.complete()
            return

        if 'photo' in msg.keys():
            self.handle_photo(message)

        if 'text' in msg.keys():
            self.handle_text(message)
        else:
            logger.log(job_id=message.job_id, error_code=20001)

    def handle_photo(self, msg: Job):
        for pic in range(msg.photo_ids):
            try:
                self.bot.download_file(msg.photo_ids[pic], msg.photo_loc[pic])
            except PermissionError as e:
                logger.log(job_id=msg.job_id, error_code=10001, error=str(e))
                self.send_now(Message("PERMISSION ERROR"))
        msg.store_photos()

    def handle_text(self, msg: Job):
        if msg.function == "no_function":
            task_queue.add_job(msg)
            logger.log(job_id=msg.job_id, error_code=30001)

        elif msg.function == "cancel":
            # todo cancel procedure. Remove from waiting list and trigger fail command
            pass

        elif msg.function in self.commands.keys():
            if type(self.commands[msg.function]) is bool:
                self.send_now(Message("That's not a command", job=msg))
                logger.log(job_id=msg.job_id, error_code=30002)
                msg.complete()
                return
            elif self.channel != main_channel and type(self.commands[msg.function]) is not str and not (self.channel in self.commands[msg.function].keys() or "all_bots" in self.commands[msg.function].keys()):
                self.send_now(Message("That command does not work on this chatbot", job=msg))
                logger.log(job_id=msg.job_id, error_code=30003)
                msg.complete()
                return

            if "function" in self.commands[msg.function].keys():
                old_func = msg.function
                msg.function = self.commands[msg.function]["function"]
                logger.log(job_id=msg.job_id, msg=f"Function updated from {old_func} to {msg.function}")

            task_queue.add_job(msg)
            logger.log(job_id=msg.job_id, msg=f"Message function verified and added {msg.function} to queue.")

        elif msg.function == "chat":
            if msg.chat_id in self.waiting_user_input.keys():
                # todo
                self.received_user_input(msg)

            else:
                self.send_now(Message("Chatbot Disabled. Type /help to find more information", job=msg))

        else:
            self.send_now(Message("Sorry, that command is not known to me...", job=msg))

    def handle_callback(self, query):
        try:
            q = str(query['data']).split(";")
        except ValueError as e:
            logger.log(job_id=0, error_code=20002, error=str(e))
            return

        try:
            msg_id = int(q[0])
        except ValueError as e:
            logger.log(job_id=0, error_code=20004, error=str(e))
            return

        logger.log(job_id=msg_id, msg='Callback Query: ' + str(query['data']))

        if q[3] == "X":
            save_loc = os.path.join(loc_telepot_callback, f"{q[0]}_cb.json")
            query = JSONEditor(save_loc).read()[f'{q[0]};{q[1]};{q[2]}']
            logger.log(job_id=msg_id, msg="Recovered Query: " + query)

            try:
                q = str(query['data']).split(";")
            except ValueError as e:
                logger.log(job_id=msg_id, error_code=20003, error=str(e))
                return

        try:
            msg = Job(job_id=msg_id)
        except LookupError as e:
            logger.log(job_id=msg_id, error_code=20005, error=str(e))
            # todo reply to callback as fail
            return

        # todo add value to collection

        task_queue.add_job(msg)

    def send_now(self, message: Message):
        message.this_telepot_account = self.channel

        replies = []
        for chat in message.chats:
            if message.photo != "":
                reply = self.bot.sendPhoto(chat,
                                           photo=open(str(message.photo), 'rb'),
                                           reply_to_message_id=message.reply_to,
                                           caption=message.send_string,
                                           reply_markup=message.keyboard)
                replies.append(reply)
            else:
                reply = self.bot.sendMessage(chat, str(message.send_string),
                                             reply_to_message_id=message.reply_to,
                                             reply_markup=message.keyboard)
                replies.append(reply)

            logger.log(job_id=message.job_id,
                       msg=f"OUTGOING: {chat}, ID: {reply['message_id']}, Message: {message.send_string}")

        message.job.add_reply(replies)

    def get_value_from_user(self, msg: Job, inquiry="value"):
        # todo get value
        pass
