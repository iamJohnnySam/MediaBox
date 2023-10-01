import datetime
import os
import feedparser
import logger
import settings
from datetime import datetime
import telepot
import global_var
from telepot.loop import MessageLoop
from editor import JSONEditor

bot = telepot.Bot(settings.telepot_id)
bot_cctv = telepot.Bot(settings.telepot_id_cctv)

telepot_settings = JSONEditor('telepot_settings.json')
telepot_connections = telepot_settings.read()

movie_search = False
movie_search_id = ""
movie_search_time = datetime.now()
movie_search_selected = False
movie_search_selected_movie = 0
movie_search_log = ["", "", "", "", "", "", "", "", "", ""]
movie_search_images = ["Error. Please Search again", "Error. Please Search again", "Error. Please Search again",
                       "Error. Please Search again", "Error. Please Search again", "Error. Please Search again",
                       "Error. Please Search again", "Error. Please Search again", "Error. Please Search again",
                       "Error. Please Search again"]


def send_to_master(msg):
    bot.sendMessage(settings.telepot_chat, msg)


def send_image_to_master(msg):
    bot.sendPhoto(settings.telepot_chat, photo=open(msg, 'rb'))


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


def handle(msg):
    global movie_search_time
    global movie_search
    global movie_search_id
    global movie_search_selected

    chat_id = msg['chat']['id']
    try:
        command = msg['text']
    except KeyError:
        logger.log('error', 'Telepot Key Error: ' + str(msg))
        return

    logger.log('info', 'Telepot: ' + str(chat_id) + ' | Got command: ' + command)

    if chat_id not in settings.allowed_chats:
        bot.sendMessage(chat_id, "Hello " + str(msg['chat']['first_name']) + "! You're not allowed to be here")
    else:
        if command == '/alive':
            bot.sendMessage(chat_id, str(chat_id))
            bot.sendMessage(chat_id, "Hello " + str(msg['chat']['first_name']) + "! I'm Alive and kicking!")
        elif command == '/time':
            bot.sendMessage(chat_id, str(datetime.datetime.now()))
        elif command == '/check_shows':
            bot.sendMessage(chat_id, "Starting TV Show Check")
            global_var.check_shows = True
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
            if chat_id == 6293292035:
                global_var.stop_cctv = True
            else:
                bot.sendMessage(chat_id, "This will reboot the program. Requesting John...")
                send_to_master("Start over requested by " + str(msg['chat']['first_name']))
                send_to_master("/start_over")
        elif command == '/find_movie':
            if movie_search or (datetime.now() - movie_search_time).total_seconds() / 3600 > 0.5:
                bot.sendMessage(chat_id, "Currently Busy. Please try again shortly")
            else:
                movie_search = True
                movie_search_id = chat_id
                movie_search_time = datetime.now()
                movie_search_selected = False
                bot.sendMessage(chat_id, "Movie Search Initiated. Time-out in 30 minutes")
                bot.sendMessage(chat_id, "To exit send /exit")
                bot.sendMessage(chat_id, "Enter the name of a movie")
        elif command == '/exit':
            if movie_search_id == chat_id:
                bot.sendMessage(chat_id, "Movie Search Ended")
                movie_search = False
        elif command == '/help' or command.lower() == 'help' or command == "/start":
            bot.sendMessage(chat_id, "--- AVAILABLE COMMANDS ---")
            bot.sendMessage(chat_id, "/alive")
            bot.sendMessage(chat_id, "/time")
            bot.sendMessage(chat_id, "/check_shows")
            bot.sendMessage(chat_id, "/check_cctv")
            bot.sendMessage(chat_id, "/add_me_to_cctv")
            bot.sendMessage(chat_id, "/add_me_to_news")
            bot.sendMessage(chat_id, "/remove_me_from_cctv")
            bot.sendMessage(chat_id, "/remove_me_from_news")
            bot.sendMessage(chat_id, "/start_over")
            bot.sendMessage(chat_id, "/find_movie")
        elif movie_search and movie_search_id == chat_id:
            handle_movie(chat_id, command)
        else:
            bot.sendMessage(chat_id, "Sorry, that command is not known to me...")


def start():
    MessageLoop(bot, handle).run_as_thread()
    print('Telepot listening')
    logger.log('info', 'Telepot listening')


def handle_movie(chat, comm):
    global movie_search_selected
    global movie_search_selected_movie
    global movie_search_log
    global movie_search_images

    if comm.lower() == "/download" and movie_search_selected:
        movie_search_selected = False
        bot.sendMessage(chat, "Movie will be added to queue")
        bot.sendMessage(chat, "Movie search has ended. Thank you...")
        send_to_master(movie_search_images[int(comm) - 1])
        send_to_master(movie_search_log[movie_search_selected_movie])
        os.system("transmission-gtk " + movie_search_log[movie_search_selected_movie])

    elif comm in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
        bot.sendMessage(chat, movie_search_images[int(comm) - 1])
        bot.sendMessage(chat, "send /download to download this movie. If not continue search")
        movie_search_selected = True
        movie_search_selected_movie = int(comm) - 1
    else:
        c = comm.lower().replace(" ", "%20")
        search_string = "https://yts.mx/rss/" + c + "/720p/all/0/en"
        send_to_master("Searching " + search_string)
        movie_feed = feedparser.parse(search_string)

        i = 1
        for x in movie_feed.entries:
            movie_search_log[i - 1] = x.links[1].href

            image_string = x.summary_detail.value
            sub1 = 'src="'
            idx1 = image_string.index(sub1)
            idx2 = image_string.index('" /></a>')
            movie_search_images[i - 1] = image_string[idx1 + len(sub1): idx2]

            bot.sendMessage(chat, i)
            i = i + 1
            bot.sendMessage(chat, x.title + " - " + x.link)
            if i == 11:
                break

        bot.sendMessage(chat, "Tell me the number of Movie you want to download")
