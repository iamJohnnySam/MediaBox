import os

import telepot
from telepot.loop import MessageLoop

from refs import db_telepot_commands, loc_telepot_callback, main_channel
from communication.message import Message
from brains.job import Job
from database_manager.json_editor import JSONEditor
from brains import task_queue
from tools.custom_exceptions import ControlledException
from tools.logger import log


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
        log(msg=f'Telepot {telepot_account} listening')

        # todo command to shutdown the bot

    def handle(self, msg):
        try:
            content = msg['text']
        except ValueError:
            content = "### No Message ###"
        log(msg=f"INCOMING: {msg['chat']['id']}, Message: {content}", log_type="info")
        message = Job(self.channel, msg)

        if not message.is_authorised:
            self.bot.sendMessage(message.chat_id, "Hello " + message.f_name + "! You're not allowed to be here")
            string = f"Unauthorised Chat access: {message.f_name}, chat_id: {message.chat_id}"
            self.send_now(Message(string))
            log(job_id=message.job_id, msg=string, log_type="warn")
            message.complete()
            return

        if 'photo' in msg.keys():
            self.handle_photo(message)

        if 'text' in msg.keys():
            self.handle_text(message)
        else:
            log(job_id=message.job_id, error_code=20001)

    def handle_photo(self, msg: Job):
        for pic in range(msg.photo_ids):
            try:
                self.bot.download_file(msg.photo_ids[pic], msg.photo_loc[pic])
            except PermissionError as e:
                log(job_id=msg.job_id, error_code=10001, error=str(e))
                self.send_now(Message("PERMISSION ERROR"))
        msg.store_photos()

    def handle_text(self, msg: Job):
        if msg.function == "no_function":
            task_queue.add_job(msg)
            log(job_id=msg.job_id, error_code=30001)

        elif msg.function == "cancel":
            if msg.chat_id in self.waiting_user_input.keys():
                self._process_waiting_list(msg, "")
                task_queue.add_job(msg)

        elif msg.function == "raise_exception" or msg.function == "shutdown":
            log(job_id=msg.job_id, msg=f"Raising controlled exception to shutdown the bot")
            raise ControlledException("Shutdown bot")

        elif msg.function in self.commands.keys():
            if type(self.commands[msg.function]) is bool:
                self.send_now(Message("That's not a command", job=msg))
                log(job_id=msg.job_id, error_code=30002)
                msg.complete()
                return

            elif self.channel != main_channel and type(self.commands[msg.function]) is not str and not (
                    self.channel in self.commands[msg.function].keys() or "all_bots" in self.commands[
                msg.function].keys()):
                self.send_now(Message("That command does not work on this chatbot", job=msg))
                log(job_id=msg.job_id, error_code=30003)
                msg.complete()
                return

            else:
                # No errors
                pass

            if "function" in self.commands[msg.function].keys():
                old_func = msg.function
                msg.function = self.commands[msg.function]["function"]
                log(job_id=msg.job_id, msg=f"Function updated from {old_func} to {msg.function}")

            else:
                # function update not required
                pass

            task_queue.add_job(msg)
            log(job_id=msg.job_id, msg=f"Message function verified and added {msg.function} to queue.")

        elif msg.function == "chat":
            if msg.chat_id in self.waiting_user_input.keys():
                self._process_waiting_list(msg)
                task_queue.add_job(msg)

            else:
                # todo
                self.send_now(Message("Chatbot Disabled. Type /help to find more information", job=msg))

        else:
            self.send_now(Message("Sorry, that command is not known to me... If you need help please send /help and I "
                                  "will send you a list of commands which you can use to start a task", job=msg))

    def _process_waiting_list(self, msg: Job, override_value=None):
        input_value = msg.user_input if override_value is None else override_value

        msg.job_id = self.waiting_user_input[msg.chat_id]["job"]
        index = self.waiting_user_input[msg.chat_id]["index"]
        msg.collect(input_value, index)
        del self.waiting_user_input[msg.chat_id]
        log(job_id=msg.job_id, msg=f"Message recalled and function, {msg.function} added to queue with "
                                   f"{input_value} collected at index {index}.")

    def handle_callback(self, query):
        try:
            q = str(query['data']).split(";")
        except ValueError as e:
            log(job_id=0, error_code=20002, error=str(e))
            return

        if q[1] == "/":
            msg_id = 0
        else:
            try:
                msg_id = int(q[0])
            except ValueError as e:
                log(job_id=0, error_code=20004, error=str(e))
                return

        log(job_id=msg_id, msg='Callback Query: ' + str(query['data']))

        if q[3] == "X":
            save_loc = os.path.join(loc_telepot_callback, f"{q[0]}_cb.json")
            query_data = JSONEditor(save_loc).read()[f'{q[0]};{q[1]};{q[2]}']
            log(job_id=msg_id, msg="Recovered Query: " + query_data)

            try:
                q = str(query_data).split(";")
            except ValueError as e:
                log(job_id=msg_id, error_code=20003, error=str(e))
                return

        if msg_id == 0:
            msg = Job(function=q[4])
            msg.collect(q[5], 0)
            task_queue.add_job(msg)
            self.bot.answerCallbackQuery(query['id'], text=f'Acknowledged!')
            return

        try:
            msg = Job(job_id=msg_id)
        except LookupError as e:
            log(job_id=msg_id, error_code=20005, error=str(e))
            self.bot.answerCallbackQuery(query['id'], text=f'FAILED! (Error 20005) [{msg_id}]')
            return

        if q[4] == '/CANCEL':
            replies = msg.replies
            for reply in replies.keys():
                self.update_keyboard(msg, replies[reply])
            msg.complete()
            self.bot.answerCallbackQuery(query['id'], text=f'Cancelled! [{msg_id}]')
            return

        elif q[4] == '/GET':
            self.get_user_input(job=msg, index=int(q[3]))
            self.update_keyboard(msg, msg.replies[q[1]])
            self.bot.answerCallbackQuery(query['id'], text=f'Type and send value! [{msg_id}]')
            return

        try:
            msg.collect(q[4], int(q[3]))
        except ValueError as e:
            log(job_id=msg_id, error_code=20004, error=str(e))
            self.bot.answerCallbackQuery(query['id'], text=f'FAILED! (Error 20004) [{msg_id}]')
            return
        except IndexError as e:
            log(job_id=msg_id, error_code=20014, error=str(e))
            self.bot.answerCallbackQuery(query['id'], text=f'FAILED! (Error 20014) [{msg_id}]')
            return

        task_queue.add_job(msg)
        self.bot.answerCallbackQuery(query['id'], text=f'Acknowledged! [{msg_id}]')
        self.update_keyboard(msg, msg.replies[q[1]])

    def send_now(self, message: Message):
        if type(message) != Message:
            log(message.job_id, error_code=20013)
            raise ValueError("Invalid data type. Expected a Message.")
        message.this_telepot_account = self.channel

        if message.job_id == 0:
            send_string = message.send_string
        else:
            send_string = f"{message.send_string}\n[{message.job_id:03}]"

        replies = []
        for chat in message.chats:
            if message.photo != "":
                try:
                    reply = self.bot.sendPhoto(chat,
                                               photo=open(str(message.photo), 'rb'),
                                               reply_to_message_id=message.reply_to,
                                               caption=str(send_string),
                                               reply_markup=message.keyboard)
                except telepot.exception.TelegramError as e:
                    log(message.job_id, error_code=20015, error=str(e))
                    continue
                replies.append(reply)
            else:
                try:
                    reply = self.bot.sendMessage(chat, str(send_string),
                                                 reply_to_message_id=message.reply_to,
                                                 reply_markup=message.keyboard)
                except telepot.exception.TelegramError as e:
                    log(message.job_id, error_code=20015, error=str(e))
                    continue
                replies.append(reply)

            log(job_id=message.job_id,
                msg=f"OUTGOING: {chat}, ID: {reply['message_id']}, Message: {message.send_string}")

        if message.job_id != 0:
            message.job.add_reply(replies)

    def get_user_input(self, job: Job, index=0):
        self.waiting_user_input[job.chat_id] = {"job": job.job_id,
                                                "index": index}
        log(job_id=job.job_id, msg=f"Waiting user input from {job.chat_id}")

    def update_keyboard(self, job: Job, msg_id, keyboard=None):
        msg: tuple = tuple(msg_id)
        try:
            self.bot.editMessageReplyMarkup(msg, reply_markup=keyboard)
            log(job_id=job.job_id, msg=f"Keyboard updated for {msg_id}")
        except telepot.exception.TelegramError as e:
            log(job_id=job.job_id, msg="No updates", log_type="warn")
