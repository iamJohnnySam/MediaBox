import logger
from datetime import datetime
import telepot
import global_var
from telepot.loop import MessageLoop

from communication.communicate_finance import CommunicateFinance
from communication.communicate_movie import CommunicateMovie

from database_manager.json_editor import JSONEditor


class Communicator:
    activity = {}
    activities = {'/find_movie': {},
                  '/expense': {}}

    def __init__(self, telepot_account):
        self.chat_name = None
        self.chat_id = None
        self.telepot_account = telepot_account
        telepot_accounts = JSONEditor('communication/telepot_accounts.json').read()
        self.bot = telepot.Bot(telepot_accounts[telepot_account]["account"])
        self.master = telepot_accounts[telepot_account]["master"]

        self.telepot_chat_id = JSONEditor('communication/telepot_groups.json')

        MessageLoop(self.bot, self.handle).run_as_thread()
        print('Telepot ', telepot_account, ' listening')
        logger.log('info', 'Telepot ' + telepot_account + 'listening')

    def send_to_group(self, group, msg, image=False):
        chats = self.telepot_chat_id.read()[group]
        for chat in chats:
            if image:
                self.bot.sendPhoto(chat, photo=open(msg, 'rb'))
            else:
                self.bot.sendMessage(chat, msg)

    def send_now(self, msg, image=False, chat=None):
        if chat is None:
            chat = self.master
        if image:
            self.bot.sendPhoto(chat, photo=open(msg, 'rb'))
        else:
            self.bot.sendMessage(chat, msg)

    def activate_mode(self, chat_id, mode):
        if (chat_id in self.activity.keys()) or (mode == '/exit'):
            self.bot.sendMessage(chat_id, "Ending Session - " + self.activity[chat_id])
            del self.activity[chat_id]

        if mode == '/exit':
            return

        self.bot.sendMessage(chat_id, "Starting Session - " + mode + "\nTo exit send /exit")
        self.activity[chat_id] = mode

        if chat_id in self.activities[mode].keys():
            del self.activities[mode][chat_id]

        if mode == "/find_movie":
            self.activities[mode][chat_id] = CommunicateMovie(self.telepot_account, chat_id)
        elif mode == "/expense":
            self.activities[mode][chat_id] = CommunicateFinance(self.telepot_account, chat_id)

    def handle(self, msg):
        self.chat_id = msg['chat']['id']
        self.chat_name = str(msg['chat']['first_name'])
        try:
            command = msg['text']
        except KeyError:
            logger.log('error', 'Telepot Key Error: ' + str(msg))
            return

        logger.log('info', 'Telepot: ' + str(self.chat_id) + ' | Got command: ' + command)
        print("MSG > " + str(self.telepot_account) + "\t" + str(self.chat_id) + "\t" + str(command))

        if str(self.chat_id) not in JSONEditor('communication/telepot_allowed_chats.json').read().keys():
            self.bot.sendMessage(self.chat_id,
                                 "Hello " + str(msg['chat']['first_name']) + "! You're not allowed to be here")
            self.send_now("Unauthorised Chat access: " + str(msg['chat']['first_name']))
        else:
            command_dictionary = JSONEditor('communication/telepot_commands_' + self.telepot_account + '.json').read()
            if command in command_dictionary.keys():
                function = command_dictionary[command]["function"]
                func = getattr(self, function)
                func()

            elif (command in self.activities.keys()) or command == '/exit':
                self.activate_mode(self.chat_id, command)

            elif self.chat_id in self.activity:
                self.activities[self.activity[self.chat_id]][self.chat_id].handle(command)

            elif command == '/help' or command.lower() == 'help' or command == "/start":
                message = "--- AVAILABLE COMMANDS ---"
                for commands in command_dictionary.keys():
                    message = message + "\n" + commands + " - " + command_dictionary[commands]["definition"]
                self.send_now(message,
                              image=False,
                              chat=self.chat_id)

            elif "/" in command:
                self.send_now("Sorry, that command is not known to me...",
                              image=False,
                              chat=self.chat_id)
            else:
                self.send_now("Sorry, I don't understand. Send /help to find out what you can do here",
                              image=False,
                              chat=self.chat_id)

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
        self.send_now("Starting TV Show Check",
                      image=False,
                      chat=self.chat_id)

    def check_news(self):
        global_var.check_news = True
        self.send_now("Starting News Check",
                      image=False,
                      chat=self.chat_id)

    def check_cctv(self):
        global_var.check_cctv = True
        self.send_now("Starting CCTV Check",
                      image=False,
                      chat=self.chat_id)

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
        else:
            self.send_now("This will shut down the program. Requesting Master User...",
                          image=False,
                          chat=self.chat_id)
            self.send_now("Start over requested by " + self.chat_name + "\n/exit_all")


telepot_channels = {}
for account in JSONEditor('communication/telepot_accounts.json').read().keys():
    telepot_channels[account] = Communicator(account)


def send_message(telepot_account, chat_id, msg, image=False):
    telepot_channels[telepot_account].send_now(msg, image, chat_id)


def send_to_master(telepot_account, msg, image=False):
    telepot_channels[telepot_account].send_now(msg, image)


def send_to_group(telepot_account, msg, group, image=False):
    telepot_channels[telepot_account].send_to_group(group, msg, image)
