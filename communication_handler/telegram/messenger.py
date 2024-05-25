import os

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from communication_handler.command_handler import Commander
from shared_models import configuration
from shared_models.message import Message
from shared_models.job import Job
from shared_tools.custom_exceptions import UnexpectedOperation
from shared_tools.image_tools import resize_image
from shared_tools.logger import log
from shared_tools.message_tools import create_keyboard_data
from shared_tools.sql_connector import SQLConnector


def create_keyboard(msg_id, function: str | list[str], reply_to, button_text: list, button_val: list,
                    arrangement: list, collection: str):
    if len(button_text) == 0 or len(button_text) != len(button_val):
        log(job_id=msg_id, error_code=20011)
        log(job_id=msg_id, msg="Button Text Length " + str(len(button_text)))
        log(job_id=msg_id, msg="Button Value Length " + str(len(button_val)))
        return

    buttons = []
    for i in range(len(button_text)):
        button_data = create_keyboard_data(msg_id=msg_id,
                                           reply_to=reply_to,
                                           function=function[i] if type(function) is list else function,
                                           button_text=button_text[i],
                                           button_value=button_val[i],
                                           collection=collection)

        buttons.append(InlineKeyboardButton(text=str(button_text[i]), callback_data=button_data))
        log(job_id=msg_id, msg=f'Keyboard button created > {button_data}')

    keyboard_markup = []
    c = 0
    for i in range(len(arrangement)):
        keyboard_row = []
        for j in range(arrangement[i]):
            keyboard_row.append(buttons[c])
            c = c + 1
        keyboard_markup.append(keyboard_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_markup)


class Messenger:

    def __init__(self, telepot_account: str, telepot_key: str, telepot_master: int):

        self.channel = telepot_account
        self.master = telepot_master

        self.config = configuration.Configuration().telegram

        # Listen
        self.bot = telepot.Bot(telepot_key)
        self.loop = MessageLoop(self.bot, {'chat': self.handle_message, 'callback_query': self.handle_callback})
        self.loop.run_as_thread()
        log(msg=f'Telepot {telepot_account} listening')

    def handle_message(self, msg: dict):
        try:
            content = msg['text']
        except ValueError:
            content = "### No Message ###"

        chat_id = msg['chat']['id']
        username = msg['chat']['first_name']

        log(msg=f"INCOMING: {chat_id}, Message: {content}", log_type="info")

        if not self.is_authorised(chat_id):
            self.bot.sendMessage(chat_id, "Hello " + username + "! You're not allowed to be here")
            string = f"Unauthorised Chat access: {username}, chat_id: {chat_id}"
            self.send_now(Message(string))
            log(msg=string, log_type="warn")
            return

        if "photo" in msg.keys():
            self.handle_photo(msg)

        Commander(msg, self.channel).process_command()

    def is_authorised(self, chat_id) -> bool:
        database = SQLConnector(job_id=0, database=self.config["database"])
        if database.check_exists(self.config["tbl_allowed_chats"], {"chat_id": chat_id}) == 0:
            return False
        else:
            return True

    def handle_photo(self, msg: dict):
        if not os.path.exists(self.config["telepot_image_dump"]):
            os.makedirs(self.config["telepot_image_dump"])

        for pic in msg['photo']:
            photo_loc = os.path.join(self.config["telepot_image_dump"], msg['photo'][pic]['file_id'])
            try:
                self.bot.download_file(msg['photo'][pic]['file_id'], photo_loc)
            except PermissionError as e:
                log(error_code=10001, error=str(e))
                self.send_now(Message("PERMISSION ERROR"))
            resize_image(job_id=0, picture_location=photo_loc)

    def handle_callback(self, query):
        log(msg='Callback Query: ' + str(query['data']))

        try:
            job, reply, get_val = Commander(query, channel=self.channel).process_callback()
        except UnexpectedOperation as e:
            log(error_code=20005, error=str(e))
            self.bot.answerCallbackQuery(query['id'], text=f'FAILED! (Error 20005)')
            return

        self.update_keyboard(job=job, msg_id=telepot.origin_identifier(query), delete_message=not get_val)
        if get_val:
            self.edit_message(job, telepot.origin_identifier(query), "Please send the value")
        self.bot.answerCallbackQuery(query['id'], text=reply)

    def send_now(self, message: Message):
        if type(message) != Message:
            log(error_code=20013)
            raise ValueError("Invalid data type. Expected a Message.")

        if message.no_message:
            log(job_id=message.msg_id, msg="Sending avoided due to background task")
            return

        chats = [message.chat_id]
        if message.group is not None:
            database = SQLConnector(self.config["database"])
            group_exists = database.check_exists(self.config["tbl_groups"], {"group_name": message.group}) != 0

            if not group_exists:
                log(job_id=message.msg_id, error_code=20007)
                raise ValueError

            result = database.select(table=self.config["tbl_groups"],
                                     columns="chat_id",
                                     where={"group_name": message.group},
                                     fetch_all=True)
            chats = [row[0] for row in result]

        if message.keyboard:
            keyboard = create_keyboard(msg_id=message.msg_id,
                                       function=message.keyboard_details["function"],
                                       reply_to=message.keyboard_details["reply_to"],
                                       button_text=message.keyboard_details["button_text"],
                                       button_val=message.keyboard_details["button_val"],
                                       arrangement=message.keyboard_details["arrangement"],
                                       collection=message.keyboard_details["collection"])
        else:
            keyboard = None

        for chat in chats:
            if message.photo != "":
                try:
                    reply = self.bot.sendPhoto(chat,
                                               photo=open(str(message.photo), 'rb'),
                                               reply_to_message_id=message.reply_to,
                                               caption=str(message.send_string),
                                               reply_markup=keyboard)
                except telepot.exception.TelegramError as e:
                    log(message.msg_id, error_code=20015, error=str(e))
                    continue
            else:
                try:
                    reply = self.bot.sendMessage(chat, str(message.send_string),
                                                 reply_to_message_id=message.reply_to,
                                                 reply_markup=keyboard)
                except telepot.exception.TelegramError as e:
                    log(message.msg_id, error_code=20015, error=str(e))
                    continue

            log(job_id=message.msg_id,
                msg=f"OUTGOING: {chat}, ID: {reply['message_id']}, Message: {message.send_string}")

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
