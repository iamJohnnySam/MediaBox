import datetime
import logger
import settings
import telepot
import global_var
from telepot.loop import MessageLoop
from editor import JSONEditor

bot = telepot.Bot(settings.telepot_id)
telepot_settings = JSONEditor('telepot_settings.json')
telepot_connections = telepot_settings.read()


def send_to_master(msg):
    bot.sendMessage(settings.telepot_chat, msg)


def send_image_to_master(msg):
    bot.sendPhoto(settings.telepot_chat, photo=open(msg, 'rb'))


def send_now(msg, chat_type, img=False):
    chats = telepot_connections[chat_type]
    for chat in chats:
        if img:
            bot.sendPhoto(chat, photo=open(msg, 'rb'))
        else:
            bot.sendMessage(chat, msg)


def handle(msg):
    chat_id = msg['chat']['id']
    try:
        command = msg['text']
    except KeyError:
        logger.log('error', 'Telepot Key Error: ' + str(msg))
        return

    logger.log('info', 'Telepot: ' + str(chat_id) + ' | Got command: ' + command)

    if command == '/alive':
        bot.sendMessage(chat_id, str(chat_id))
        bot.sendMessage(chat_id, "Hello " + str(msg['chat']['first_name']) + "! I'm Alive and kicking!")
    elif command == '/time':
        bot.sendMessage(chat_id, str(datetime.datetime.now()))
    elif command == '/check-shows':
        bot.sendMessage(chat_id, "Starting TV Show Check")
        global_var.check_shows = True
    elif command == '/check-cctv':
        bot.sendMessage(chat_id, "Starting CCTV Check")
        global_var.check_cctv = True
    elif command == '/add-me-to-cctv':
        bot.sendMessage(chat_id, "Not Implemented")
    elif command == '/add-me-to-news':
        bot.sendMessage(chat_id, "Not Implemented")
    elif command == '/remove-me-from-cctv':
        bot.sendMessage(chat_id, "Not Implemented")
    elif command == '/remove-me-from-cctv':
        bot.sendMessage(chat_id, "Not Implemented")

    elif command == '/help':
        bot.sendMessage(chat_id, "--- AVAILABLE COMMANDS ---")
        bot.sendMessage(chat_id, "/alive")
        bot.sendMessage(chat_id, "/time")
        bot.sendMessage(chat_id, "/check-shows")
        bot.sendMessage(chat_id, "/check-cctv")
        bot.sendMessage(chat_id, "/add-me-to-cctv")
        bot.sendMessage(chat_id, "/add-me-to-news")
        bot.sendMessage(chat_id, "/remove-me-from-cctv")
        bot.sendMessage(chat_id, "/remove-me-from-news")
    else:
        bot.sendMessage(chat_id, "Sorry, that command is not known to me...")


def start():
    MessageLoop(bot, handle).run_as_thread()
    print('Telepot listening')
    logger.log('info', 'Telepot listening')
