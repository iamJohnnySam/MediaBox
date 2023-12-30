import threading
import feedparser
import logger
from datetime import datetime
import global_var

from telepot.namedtuple import InlineKeyboardMarkup

from communication.communicator_base import CommunicatorBase
from database_manager import sql_connector
from database_manager.json_editor import JSONEditor
from show import transmission


# os.environ['_BARD_API_KEY'] = settings.bard


class Communicator(CommunicatorBase):

    def __init__(self, telepot_account):
        super().__init__(telepot_account)

    def alive(self, msg, chat_id, message_id, value):
        self.send_now(str(chat_id) + "\n" + "Hello " + str(msg['chat']['first_name']) + "! I'm Alive and kicking!",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def time(self, msg, chat_id, message_id, value):
        self.send_now(str(datetime.now()),
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def check_shows(self, msg, chat_id, message_id, value):
        global_var.check_shows = True
        self.send_now("Request Initiated - TV Show Check",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def check_news(self, msg, chat_id, message_id, value):
        global_var.check_news = True
        self.send_now("Request Initiated - News Check",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def check_cctv(self, msg, chat_id, message_id, value):
        global_var.check_cctv = True
        self.send_now("Request Initiated - CCTV Check",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def find_movie(self, msg, chat_id, message_id, value):
        movie = value

        if movie == "":
            self.send_now("Please type the name of the movie after the command. You can press and hold this "
                          "command and type the movie \n /find_movie", chat=chat_id, reply_to=message_id)
            return

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

            key1_id, key1_button = self.keyboard_button("See Image", "echo", image)
            key2_id, key2_button = self.keyboard_button("Visit Page", "echo", x.link)
            key3_id, key3_button = self.keyboard_button("Cancel", "cancel", "")
            key4_id, key4_button = self.keyboard_button("Download", "download", x.links[1].href)

            keyboard = InlineKeyboardMarkup(inline_keyboard=[[key1_button, key2_button, key3_button],
                                                             [key4_button]])

            message = self.send_now(x.title, chat=chat_id, keyboard=keyboard)

            self.link_msg_to_buttons(message, [key1_id, key2_id, key3_id, key4_id])

    def finance(self, msg, chat_id, message_id, value):
        if value == "":
            self.send_now("Please type the amount after the command. You can press and hold this "
                          "command and type the amount\n /finance", chat=chat_id, reply_to=message_id)
            return

        sql_id = sql_connector.insert('transactions', "amount", str(value), 'finance')
        identifier = "transactions_" + str(sql_id) + "_"

        key1_id, key1_button = self.keyboard_button("Income", "finance", identifier + "income")
        key2_id, key2_button = self.keyboard_button("Expense", "finance", identifier + "expense")
        key3_id, key3_button = self.keyboard_button("Invest", "finance", identifier + "invest")
        key4_id, key4_button = self.keyboard_button("Delete", "finance", identifier + "delete")

        keyboard_markup = [[key1_button, key2_button, key3_button],
                           [key4_button]]

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)

        message = self.send_now("Let's fill some missing info", chat=chat_id, keyboard=keyboard,
                                reply_to=message_id)

        self.link_msg_to_buttons(message, [key1_id, key2_id, key3_id, key4_id])

    def request_tv_show(self, msg, chat_id, message_id, value):
        show = value
        if show == "":
            self.send_now("Please type the name of the tv show after the command. You can press and hold this "
                          "command and type the movie \n /request_tv_show", chat=chat_id)
            return

        request = {show: str(msg['chat']['first_name'])}
        JSONEditor('database/requested_shows.json').add_level1(request)
        logger.log("TV Show Requested - " + show)
        self.send_now("TV Show Requested - " + show, chat=chat_id, reply_to=message_id)

    def add_me_to_cctv(self, msg, chat_id, message_id, value):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def add_me_to_news(self, msg, chat_id, message_id, value):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def remove_me_from_cctv(self, msg, chat_id, message_id, value):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def remove_me_from_news(self, msg, chat_id, message_id, value):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def list_torrents(self, msg, chat_id, message_id, value):
        torrent_list = transmission.list_all()
        self.send_now(str(torrent_list),
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_feed(self, msg, chat_id, message_id, value):
        identifier = "baby_" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "_"

        if value == "":
            self.send_now("Please type the amount after the command. You can press and hold this "
                          "command and type the amount\n /finance", chat=chat_id, reply_to=message_id)
        else:
            key1_id, key1_button = self.keyboard_button("Breast", "baby_feed", identifier + value + "_breast")
            key2_id, key2_button = self.keyboard_button("Formula", "baby_feed", identifier + value + "_bottle")
            key3_id, key3_button = self.keyboard_button("Cancel", "cancel", "")

            keyboard_markup = [[key1_button, key2_button], [key3_button]]
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)

            message = self.send_now("Let's fill some missing info", chat=chat_id, keyboard=keyboard,
                                    reply_to=message_id)

            self.link_msg_to_buttons(message, [key1_id, key2_id, key3_id])

    def start_over(self, msg, chat_id, message_id, value):
        if chat_id == self.master:
            global_var.stop_cctv = True
        else:
            self.send_now("This will reboot the program. Requesting Master User...",
                          image=False,
                          chat=chat_id,
                          reply_to=message_id)
            self.send_now("Start over requested by " + str(msg['chat']['first_name']) + "\n/start_over")

    def exit_all(self, msg, chat_id, message_id, value):
        if chat_id == self.master:
            global_var.stop_all = True
            global_var.stop_cctv = True
            self.send_now("Completing ongoing tasks. Please wait.")
        else:
            self.send_now("This will shut down the program. Requesting Master User...",
                          image=False,
                          chat=chat_id,
                          reply_to=message_id)
            self.send_now("Start over requested by " + str(msg['chat']['first_name']) + "\n/exit_all")

    def reboot_pi(self, msg, chat_id, message_id, value):
        if chat_id == self.master:
            global_var.stop_all = True
            global_var.stop_cctv = True
            global_var.reboot_pi = True
            self.send_now("Completing ongoing tasks. Please wait.")
        else:
            self.send_now("This will reboot the server. Requesting Master User...",
                          image=False,
                          chat=chat_id,
                          reply_to=message_id)
            self.send_now("Start over requested by " + str(msg['chat']['first_name']) + "\n/reboot_pi")

    # -------------- CALLBACK FUNCTIONS --------------

    def cb_cancel(self, callback_id, query_id, from_id, value):
        self.update_in_line_buttons(callback_id)
        self.bot.answerCallbackQuery(query_id, text='Canceled')

    def cb_echo(self, callback_id, query_id, from_id, value):
        self.send_now(value, chat=from_id)
        self.bot.answerCallbackQuery(query_id, text='Sent')

    def cb_download(self, callback_id, query_id, from_id, value):
        success, torrent_id = transmission.download(value)
        if success:
            self.update_in_line_buttons(callback_id)
            self.send_now("Movie will be added to queue", chat=from_id)
        self.bot.answerCallbackQuery(query_id, text='Downloaded')

    def cb_finance(self, callback_id, query_id, from_id, value):
        pass


telepot_lock = threading.Lock()

telepot_channels = {}
for account in JSONEditor('communication/telepot_accounts.json').read().keys():
    telepot_channels[account] = Communicator(account)


def send_message(telepot_account, chat_id, msg, image=False, caption=""):
    telepot_lock.acquire()
    msg_id = telepot_channels[telepot_account].send_now(msg, image, chat_id, caption=caption)
    logger.log(str(chat_id) + " - " + str(msg), source="TG-R")
    telepot_lock.release()
    return msg_id


def send_to_master(telepot_account, msg, image=False, caption=""):
    telepot_lock.acquire()
    msg_id = telepot_channels[telepot_account].send_now(msg, image, caption=caption)
    telepot_lock.release()
    return msg_id


def send_to_group(telepot_account, msg, group, image=False, caption=""):
    telepot_lock.acquire()
    telepot_channels[telepot_account].send_to_group(group, msg, image, caption=caption)
    telepot_lock.release()
