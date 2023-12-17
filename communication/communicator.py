import os
import threading

import feedparser

import logger
from datetime import datetime
import global_var
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InlineQueryResultArticle, InputTextMessageContent
import openai
import settings
from communication.communicate_finance import CommunicateFinance
from communication.communicate_movie import CommunicateMovie
from communication.communicator_ai import TalkToAI
from database_manager.json_editor import JSONEditor
from show import transmission

openai.my_api_key = settings.chat


class Communicator:

    def __init__(self, telepot_account):
        self.allowed_chats = None
        self.telepot_groups = {}
        self.ai_messages = {}
        self.activity = {}
        self.activities = {'/find_movie': {},
                           '/expense': {}}
        self.chat_name = None
        self.chat_id = None
        self.message = None
        self.callback_id_prefix = str(datetime.now()) + "_"
        self.current_callback_id = 0

        self.telepot_account = telepot_account
        telepot_accounts = JSONEditor('communication/telepot_accounts.json').read()
        self.bot = telepot.Bot(telepot_accounts[telepot_account]["account"])
        self.master = telepot_accounts[telepot_account]["master"]

        self.telepot_chat_id = JSONEditor('communication/telepot_groups.json')

        self.command_dictionary = JSONEditor('communication/telepot_commands_' + self.telepot_account + '.json').read()

        MessageLoop(self.bot, {'chat': self.handle,
                               'callback_query': self.handle_callback}).run_as_thread()
        logger.log('Telepot ' + telepot_account + ' listening', source="TG")

    def send_to_group(self, group, msg, image=False):
        if self.telepot_groups == {}:
            self.telepot_groups = self.telepot_chat_id.read()

        chats = self.telepot_groups[group]

        logger.log(str(chats) + " - Group Message: " + msg, "TG")

        for chat in chats:
            if image:
                self.bot.sendPhoto(chat, photo=open(msg, 'rb'))
            else:
                self.bot.sendMessage(chat, msg)

    def send_now(self, msg, image=False, chat=None, keyboard=None):
        if msg == "":
            logger.log("NO MESSAGE", source="TG", message_type="error")
            return

        if chat is None:
            chat = self.master

        logger.log(str(chat) + " - Message: " + msg, "TG")

        if image:
            self.bot.sendPhoto(chat, photo=open(msg, 'rb'))
        else:
            self.bot.sendMessage(chat, msg)

        if keyboard is not None:
            self.current_callback_id = self.current_callback_id + 1
            self.bot.sendMessage(chat, 'Use inline keyboard', reply_markup=keyboard)

    # def activate_mode(self, chat_id, mode):
    #     if (chat_id in self.activity.keys()) or (mode == '/exit'):
    #         self.bot.sendMessage(chat_id, "Ending Session - " + self.activity[chat_id])
    #         logger.log(str(chat_id) + " - Ending Session - " + self.activity[chat_id], source="TG")
    #         del self.activity[chat_id]
    #
    #     if mode == '/exit':
    #         return
    #
    #     self.bot.sendMessage(chat_id, "Starting Session - " + mode + "\nTo exit send /exit")
    #     self.activity[chat_id] = mode
    #     logger.log(str(chat_id) + " - Starting Session - " + self.activity[chat_id], source="TG")
    #
    #     if chat_id in self.activities[mode].keys():
    #         del self.activities[mode][chat_id]
    #
    #     if mode == "/find_movie":
    #         self.activities[mode][chat_id] = CommunicateMovie(self.telepot_account, chat_id)
    #     elif mode == "/expense":
    #         self.activities[mode][chat_id] = CommunicateFinance(self.telepot_account, chat_id)

    def keyboard_button(self, text, callback_command, value = "None"):
        data = self.callback_id_prefix + str(self.current_callback_id)
        data = data + "," + str(callback_command) + "," + str(value)
        return InlineKeyboardButton(text=str(text), callback_data=data)

    def check_allowed_sender(self, chat_id, msg):
        # Load allowed list of chats first time
        if self.allowed_chats is None:
            self.allowed_chats = JSONEditor('communication/telepot_allowed_chats.json').read().keys()

        if str(chat_id) in self.allowed_chats:
            return True
        else:
            self.bot.sendMessage(self.chat_id,
                                 "Hello " + str(msg['chat']['first_name']) + "! You're not allowed to be here")
            self.send_now("Unauthorised Chat access: " + str(msg['chat']['first_name']))
            logger.log("Unauthorised Chat access: " + str(msg['chat']['first_name']), source="TG", message_type="warn")
            return False

    def handle(self, msg):
        # Get Command details
        self.chat_id = msg['chat']['id']
        self.chat_name = str(msg['chat']['first_name'])
        try:
            self.message = str(msg['text'])
            command = self.message.split(" ")[0]
        except KeyError:
            logger.log('Telepot Key Error: ' + str(msg), source="TG", message_type="error")
            return

        logger.log(str(self.telepot_account) + "\t" + str(self.chat_id) + " - " + str(command), source="MSG")

        # Check if sender is in allowed list
        if self.check_allowed_sender(self.chat_id, msg):

            # If command is in command list
            if command in self.command_dictionary.keys():
                function = self.command_dictionary[command]["function"]
                logger.log(str(self.chat_id) + ' - Calling Function: ' + function, source="TG")
                func = getattr(self, function)
                func()

            # If command is not in list or if /exit
            # elif (command in self.activities.keys()) or command == '/exit':
            #     self.activate_mode(self.chat_id, command)

            elif self.chat_id in self.activity:
                self.activities[self.activity[self.chat_id]][self.chat_id].handle(command)

            elif command == '/help' or command.lower() == 'help' or command == "/start":
                message = "--- AVAILABLE COMMANDS ---"
                for commands in self.command_dictionary.keys():
                    message = message + "\n" + commands + " - " + self.command_dictionary[commands]["definition"]
                message = message + "\n\n ACTIVITIES"
                for commands in self.activities.keys():
                    message = message + "\n" + commands

                self.send_now(message,
                              image=False,
                              chat=self.chat_id)

            elif "/" in command:
                self.send_now("Sorry, that command is not known to me...",
                              image=False,
                              chat=self.chat_id)
            else:
                # self.talk_to_ai(self.chat_id, command)
                self.send_now("Sorry, Talk to AI is disabled. Please try a different command",
                              image=False,
                              chat=self.chat_id)

    def handle_callback(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        logger.log('Callback Query: ' + " " + query_id + " " + from_id + " " + query_data)

        callback_id = str(query_data).split(",")[0]
        command = str(query_data).split(",")[1]
        value = str(query_data).split(",")[2]

        if command == "cancel":
            self.bot.answerCallbackQuery(query_id, text='Canceled')
        elif command == "echo":
            self.send_now(value, chat=from_id)
        elif command == "download":
            success, torrent_id = transmission.download(value)
            if success:
                self.send_now("Movie will be added to queue", chat=from_id)
        else:
            self.bot.answerCallbackQuery(query_id, text='Unhandled')

    def alive(self):
        self.send_now(str(self.chat_id) + "\n" + "Hello " + self.chat_name + "! I'm Alive and kicking!",
                      image=False,
                      chat=self.chat_id)

    def time(self):
        self.send_now(str(datetime.now()),
                      image=False,
                      chat=self.chat_id)

    def check_shows(self):
        global_var.check_shows = True
        self.send_now("Request Initiated - TV Show Check",
                      image=False,
                      chat=self.chat_id)

    def check_news(self):
        global_var.check_news = True
        self.send_now("Request Initiated - News Check",
                      image=False,
                      chat=self.chat_id)

    def check_cctv(self):
        global_var.check_cctv = True
        self.send_now("Request Initiated - CCTV Check",
                      image=False,
                      chat=self.chat_id)

    def find_movie(self):
        movie = self.message.replace(self.message.split(" ")[0], "").trim()
        movie = movie.lower().replace(" ", "%20")
        movie = movie.lower().replace("/", "")
        search_string = "https://yts.mx/rss/" + movie + "/720p/all/0/en"

        self.send_now("Searching " + search_string)
        logger.log("Searching " + search_string, source="MOV")
        movie_feed = feedparser.parse(search_string)

        for x in movie_feed.entries:
            image_string = x.summary_detail.value
            sub1 = 'src="'
            idx1 = image_string.index(sub1)
            idx2 = image_string.index('" /></a>')
            image = image_string[idx1 + len(sub1): idx2]

            keyboard = InlineKeyboardMarkup(self.keyboard_button("See Image", "echo", image),
                                            self.keyboard_button("Visit Page", "echo", x.link),
                                            self.keyboard_button("Download", "download", x.links[1].href),
                                            self.keyboard_button("Not This", "cancel"))

            self.send_now(x.title, chat=self.chat_id, keyboard=keyboard)

    def add_me_to_cctv(self):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=self.chat_id)

    def add_me_to_news(self):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=self.chat_id)

    def remove_me_from_cctv(self):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=self.chat_id)

    def remove_me_from_news(self):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=self.chat_id)

    def current_activity(self):
        if self.chat_id in self.activity.keys():
            self.send_now("Current activity is " + self.activity[self.chat_id],
                          image=False,
                          chat=self.chat_id)
        else:
            self.send_now("No current activity",
                          image=False,
                          chat=self.chat_id)

    def list_torrents(self):
        torrent_list = transmission.list_all()
        self.send_now(str(torrent_list),
                      image=False,
                      chat=self.chat_id)

    def start_over(self):
        if self.chat_id == self.master:
            global_var.stop_cctv = True
        else:
            self.send_now("This will reboot the program. Requesting Master User...",
                          image=False,
                          chat=self.chat_id)
            self.send_now("Start over requested by " + self.chat_name + "\n/start_over")

    def exit_all(self):
        if self.chat_id == self.master:
            global_var.stop_all = True
            global_var.stop_cctv = True
            self.send_now("Completing ongoing tasks. Please wait.")
        else:
            self.send_now("This will shut down the program. Requesting Master User...",
                          image=False,
                          chat=self.chat_id)
            self.send_now("Start over requested by " + self.chat_name + "\n/exit_all")

    def reboot_pi(self):
        if self.chat_id == self.master:
            global_var.stop_all = True
            global_var.stop_cctv = True
            global_var.reboot_pi = True
            self.send_now("Completing ongoing tasks. Please wait.")
        else:
            self.send_now("This will reboot the server. Requesting Master User...",
                          image=False,
                          chat=self.chat_id)
            self.send_now("Start over requested by " + self.chat_name + "\n/reboot_pi")

    def talk_to_ai(self, chat_id, command):
        if str(self.chat_id) not in self.ai_messages.keys():
            self.ai_messages[str(chat_id)] = TalkToAI(self.chat_id)

        self.ai_messages[str(chat_id)].send_to_ai(command)


telepot_lock = threading.Lock()

telepot_channels = {}
for account in JSONEditor('communication/telepot_accounts.json').read().keys():
    telepot_channels[account] = Communicator(account)


def send_message(telepot_account, chat_id, msg, image=False):
    telepot_lock.acquire()
    telepot_channels[telepot_account].send_now(msg, image, chat_id)
    logger.log(str(chat_id) + " - " + str(msg), source="TG-R")
    telepot_lock.release()


def send_to_master(telepot_account, msg, image=False):
    telepot_lock.acquire()
    telepot_channels[telepot_account].send_now(msg, image)
    telepot_lock.release()


def send_to_group(telepot_account, msg, group, image=False):
    telepot_lock.acquire()
    telepot_channels[telepot_account].send_to_group(group, msg, image)
    telepot_lock.release()
