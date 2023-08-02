import datetime
import logger
import settings
import telepot
import global_var
from telepot.loop import MessageLoop

bot = telepot.Bot(settings.telepot_id)


def send_now(msg):
    bot.sendMessage(settings.telepot_chat, msg)


def send_image(msg):
    bot.sendPhoto(settings.telepot_chat, photo=open(msg, 'rb'))


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
    else:
        bot.sendMessage(chat_id, "Sorry, that command is not known to me...")


def start():
    MessageLoop(bot, handle).run_as_thread()
    logger.log('info', 'Telepot listening')
