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
    command = msg['text']

    logger.log('info', 'Telepot: ' + str(chat_id) + ' | Got command: ' + command)

    if command == '/alive':
        bot.sendMessage(chat_id, str(chat_id) + " - I'm Alive!")
    elif command == '/time':
        bot.sendMessage(chat_id, str(datetime.datetime.now()))
    elif command == '/checkshows':
        bot.sendMessage(chat_id, "Starting TV Show Check")
        global_var.check_shows = True
    elif command == '/addmetocctv':
        pass
    else:
        bot.sendMessage(chat_id, "Sorry, that command is not known to me...")


def start():
    MessageLoop(bot, handle).run_as_thread()
    print('Telepot listening')
    logger.log('info', 'Telepot listening')
