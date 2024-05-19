import os
import sys
import threading

import telepot
from telepot.loop import MessageLoop

from shared_models import configuration
from shared_models.message import Message
from shared_models.job import Job
from shared_tools.json_editor import JSONEditor
from job_handler import task_queue
from shared_tools.logger import log


class Messenger:

    def __init__(self, telepot_account: str, telepot_key: str, telepot_master: int):
        self.channel = telepot_account
        self.master = telepot_master

        self.config = configuration.Configuration().telegram

        # Waiting user input
        self.waiting_user_input = {}

        # Get Commands
        self.commands = JSONEditor(refs.db_telepot_commands).read()

        # Listen
        self.bot = telepot.Bot(telepot_key)
        self.loop = MessageLoop(self.bot, {'chat': self.handle, 'callback_query': self.handle_callback})
        self.loop.run_as_thread()
        log(msg=f'Telepot {telepot_account} listening')

        self.shutdown_attempted = False

        # todo command to shutdown the bot

    def handle(self, msg):
        self.shutdown()
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
                msg.job_id = self.waiting_user_input[msg.chat_id]["job"]
                del self.waiting_user_input[msg.chat_id]
                self.send_now(Message(f"Job canceled.", msg))
                msg.complete()

        elif msg.function == "raise_exception" or msg.function == "shutdown":
            shutdown_bot[self.channel] = True
            self.shutdown()

        elif msg.function in self.commands.keys():
            if type(self.commands[msg.function]) is bool:
                self.send_now(Message("That's not a command", job=msg))
                log(job_id=msg.job_id, error_code=30002)
                msg.complete()
                return

            elif self.channel != params.get_param('telepot', 'main_channel') and \
                    type(self.commands[msg.function]) is not str and \
                    not (self.channel in self.commands[msg.function].keys() or
                         "all_bots" in self.commands[msg.function].keys()):
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
                msg.called_back = True
                task_queue.add_job(msg)

            else:
                # todo
                self.send_now(Message("Chatbot Disabled. Type /help to find more information", job=msg))

        else:
            self.send_now(Message("Sorry, that command is not known to me... If you need help please send /help and I "
                                  "will send you a list of commands which you can use to start a task", job=msg))

    def _process_waiting_list(self, msg: Job, override_value=None):
        input_value = msg.user_input if override_value is None else override_value

        if self.waiting_user_input[msg.chat_id]["job"] == 0:
            msg.function = self.waiting_user_input[msg.chat_id]["function"]
        else:
            msg.job_id = self.waiting_user_input[msg.chat_id]["job"]
        index = self.waiting_user_input[msg.chat_id]["index"]
        msg.collect(input_value, index)
        del self.waiting_user_input[msg.chat_id]
        log(job_id=msg.job_id, msg=f"Message recalled and function, {msg.function} added to queue with "
                                   f"{input_value} collected at index {index}.")

    def handle_callback(self, query):
        self.shutdown()
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
            save_loc = os.path.join(refs.loc_telepot_callback, f"{q[0]}_cb.json")
            query_data = JSONEditor(save_loc).read()[f'{q[0]};{q[1]};{q[2]}']
            log(job_id=msg_id, msg="Recovered Query: " + query_data)

            try:
                q = str(query_data).split(";")
            except ValueError as e:
                log(job_id=msg_id, error_code=20003, error=str(e))
                return

        if msg_id == 0:
            msg = Job(function=q[3], chat_id=query['from']['id'], username=query['from']['first_name'],
                      telepot_account=self.channel)
        else:
            try:
                msg = Job(job_id=msg_id)
            except LookupError as e:
                log(job_id=msg_id, error_code=20005, error=str(e))
                self.bot.answerCallbackQuery(query['id'], text=f'FAILED! (Error 20005) [{msg_id}]')
                return

        if q[4] == '/CANCEL':
            self.update_keyboard(msg, telepot.origin_identifier(query))
            msg.complete()
            self.bot.answerCallbackQuery(query['id'], text=f'Cancelled! [{msg_id}]')
            return

        elif q[4] == '/GET':
            if msg.job_id == 0:
                self.get_user_input(job=msg, index=0)
            else:
                self.get_user_input(job=msg, index=int(q[3]))
            self.update_keyboard(msg, telepot.origin_identifier(query), delete_message=False)
            self.edit_message(msg, telepot.origin_identifier(query), "Please send the value")
            self.bot.answerCallbackQuery(query['id'], text=f'Type and send value! [{msg_id}]')
            return

        try:
            if msg.job_id == 0:
                msg.collect(q[4], 0)
            else:
                msg.collect(q[4], int(q[3]))
        except ValueError as e:
            log(job_id=msg_id, error_code=20004, error=str(e))
            self.bot.answerCallbackQuery(query['id'], text=f'FAILED! (Error 20004) [{msg_id}]')
            return
        except IndexError as e:
            log(job_id=msg_id, error_code=20014, error=str(e))
            self.bot.answerCallbackQuery(query['id'], text=f'FAILED! (Error 20014) [{msg_id}]')
            return

        msg.called_back = True
        task_queue.add_job(msg)
        self.bot.answerCallbackQuery(query['id'], text=f'Acknowledged! [{msg_id}]')

        self.update_keyboard(msg, telepot.origin_identifier(query))
        # self.update_keyboard(msg, msg.replies[q[1]])

    def send_now(self, message: Message):
        if message.job is not None and message.job.is_background_task:
            log(job_id=message.job_id, msg="Sending avoided due to background task")
            return

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

        if message.job is not None and message.job_id != 0:
            message.job.add_reply(replies)

    def get_user_input(self, job: Job, index=0):
        self.waiting_user_input[job.chat_id] = {"job": job.job_id,
                                                "index": index,
                                                "function": job.function}
        log(job_id=job.job_id, msg=f"Waiting user input from {job.chat_id}")

    def update_keyboard(self, job: Job, msg_id, keyboard=None, delete_message: bool = True):
        msg: tuple = tuple(msg_id)
        if keyboard is None and delete_message:
            try:
                self.bot.deleteMessage(msg)
                log(job_id=job.job_id, msg=f"Message Deleted: {msg_id}")
            except telepot.exception.TelegramError as e:
                log(job_id=job.job_id, msg=f"No updates - {str(e)}", log_type="warn")
        else:
            try:
                self.bot.editMessageReplyMarkup(msg, reply_markup=keyboard)
                log(job_id=job.job_id, msg=f"Keyboard updated for {msg_id}")
            except telepot.exception.TelegramError as e:
                log(job_id=job.job_id, msg=f"No updates - {str(e)}", log_type="warn")

    def edit_message(self, job: Job, msg_id, new_message):
        msg: tuple = tuple(msg_id)
        try:
            self.bot.editMessageText(msg, text=new_message)
            log(job_id=job.job_id, msg=f"Message {msg_id} updated to {new_message}")
        except telepot.exception.TelegramError as e:
            log(job_id=job.job_id, msg=f"Could not update message {msg_id} - {str(e)}", log_type="warn")

    def shutdown(self):
        if self.channel in shutdown_bot.keys():
            log(msg=f"This bot will attempt to shutdown - Thread ID = {threading.get_ident()}", log_type="info")
            if self.shutdown_attempted:
                self.send_now(Message(f"{self.channel.capitalize()} Bot previous shutdown attempt failed. "
                                      f"Continuation is blocked.\nReattempting shutdown..."))
            else:
                self.send_now(Message(f"{self.channel.capitalize()} Bot attempt to shutdown.."))
            self.shutdown_attempted = True
            del self.loop
            sys.exit()
