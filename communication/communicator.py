import logger
import settings
from datetime import datetime
import telepot
import global_var
from telepot.loop import MessageLoop

from communication.communicate_finance import CommunicateFinance
from communication.communicate_movie import CommunicateMovie

from database_manager.json_editor import JSONEditor


class Communicator:
    def __init__(self, telepot_account):
        telepot_accounts = JSONEditor('communication/telepot_accounts.json').read()
        self.bot = telepot.Bot(telepot_accounts[telepot_account]["account"])
        self.master = telepot_accounts[telepot_account]["master"]

    def send_to_master(self, msg, image=False):
        if image:
            self.bot.sendPhoto(self.master, photo=open(msg, 'rb'))
        else:
            self.bot.sendMessage(self.master, msg)


telepot_accounts = JSONEditor('communication/telepot_accounts.json').read()
bot = telepot.Bot(telepot_accounts["main"]["account"])
bot_cctv = telepot.Bot(telepot_accounts["cctv"]["account"])

telepot_settings = JSONEditor('communication/telepot_comms.json')
telepot_connections = telepot_settings.read()

# Activity Dictionaries
activity = {}
activities = {'/find_movie': {},
              '/expense': {}}


def send_to_master(msg):
    bot.sendMessage(settings.master_chat, msg)


def send_message(chat_id, msg):
    bot.sendMessage(chat_id, msg)


def send_now(msg, chat_type, img=False, cctv=True):
    chats = telepot_connections[chat_type]
    for chat in chats:
        if img:
            if cctv:
                bot_cctv.sendPhoto(chat, photo=open(msg, 'rb'))
            else:
                bot.sendPhoto(chat, photo=open(msg, 'rb'))
        else:
            if cctv:
                bot_cctv.sendMessage(chat, msg)
            else:
                bot.sendMessage(chat, msg)


def activate_mode(chat_id, mode):
    global activity
    global activities

    if (chat_id in activity.keys()) or (mode == '/exit'):
        bot.sendMessage(chat_id, "Ending Session - " + activity[chat_id])
        del activity[chat_id]

    if mode == '/exit':
        return

    bot.sendMessage(chat_id, "Starting Session - " + mode + "\nTo exit send /exit")
    activity[chat_id] = mode

    if chat_id in activities[mode].keys():
        del activities[mode][chat_id]

    if mode == "/find_movie":
        activities[mode][chat_id] = CommunicateMovie(chat_id)
    elif mode == "/expense":
        activities[mode][chat_id] = CommunicateFinance(chat_id)


def handle(msg):
    global activities
    global activity

    chat_id = msg['chat']['id']
    try:
        command = msg['text']
    except KeyError:
        logger.log('error', 'Telepot Key Error: ' + str(msg))
        return

    logger.log('info', 'Telepot: ' + str(chat_id) + ' | Got command: ' + command)

    if chat_id not in settings.allowed_chats:
        bot.sendMessage(chat_id, "Hello " + str(msg['chat']['first_name']) + "! You're not allowed to be here")
        send_to_master("Unauthorised Chat access: " + str(msg['chat']['first_name']))
    else:
        if command == '/alive':
            bot.sendMessage(chat_id, str(chat_id) + "\n" +
                            "Hello " + str(msg['chat']['first_name']) + "! I'm Alive and kicking!")

        elif command == '/time':
            bot.sendMessage(chat_id, str(datetime.now()))

        elif command == '/check_shows':
            bot.sendMessage(chat_id, "Starting TV Show Check")
            global_var.check_shows = True

        elif command == '/check_news':
            bot.sendMessage(chat_id, "Starting News Check")
            global_var.check_news = True

        elif command == '/check_cctv':
            bot.sendMessage(chat_id, "Starting CCTV Check")
            global_var.check_cctv = True

        elif command == '/add_me_to_cctv':
            bot.sendMessage(chat_id, "Not Implemented")

        elif command == '/add_me_to_news':
            bot.sendMessage(chat_id, "Not Implemented")

        elif command == '/remove_me_from_cctv':
            bot.sendMessage(chat_id, "Not Implemented")

        elif command == '/remove_me_from_cctv':
            bot.sendMessage(chat_id, "Not Implemented")

        elif command == '/start_over':
            if chat_id == settings.master_chat:
                global_var.stop_cctv = True
            else:
                bot.sendMessage(chat_id, "This will reboot the program. Requesting John...")
                send_to_master("Start over requested by " + str(msg['chat']['first_name']) + "\n/start_over")

        elif command == '/exit_all' and chat_id == settings.master_chat:
            global_var.stop_all = True
            global_var.stop_cctv = True

        elif command == '/current_activity':
            if chat_id in activity.keys():
                bot.sendMessage(chat_id, "Current activity is " + activity[chat_id])
            else:
                bot.sendMessage(chat_id, "No current activity")

        elif (command in activities.keys()) or command == '/exit':
            activate_mode(chat_id, command)

        elif command == '/help' or command.lower() == 'help' or command == "/start":
            bot.sendMessage(chat_id,
                            "--- AVAILABLE COMMANDS ---\n" +
                            "/alive\n" +
                            "/time\n" +
                            "/current_activity\n" +
                            "\n" +
                            "/check_shows\n" +
                            "/find_movie\n" +
                            "\n" +
                            "/check_cctv\n" +
                            "/add_me_to_cctv\n" +
                            "/remove_me_from_cctv\n" +
                            "\n" +
                            "/check_news\n" +
                            "/remove_me_from_news\n" +
                            "\n" +
                            "/expense\n" +
                            "\n" +
                            "/start_over\n"
                            "/exit_all"
                            )

        elif chat_id in activity:
            activities[activity[chat_id]][chat_id].handle(command)

        elif "/" in command:
            bot.sendMessage(chat_id, "Sorry, that command is not known to me...")

        else:
            bot.sendMessage(chat_id, "Sorry, I don't understand. Send /help to find out what you can do here")


def start():
    MessageLoop(bot, handle).run_as_thread()
    print('Telepot listening')
    logger.log('info', 'Telepot listening')
