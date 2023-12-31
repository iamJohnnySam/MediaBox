import threading
import feedparser
import telepot

import logger
from datetime import datetime, timedelta
import global_var
from charts.grapher import grapher_category_dictionary, grapher_trend

from communication.communicator_base import CommunicatorBase
from database_manager import sql_connector
from database_manager.json_editor import JSONEditor
from show import transmission


# os.environ['_BARD_API_KEY'] = settings.bard


class Communicator(CommunicatorBase):

    def __init__(self, telepot_account):
        super().__init__(telepot_account)
        self.source = "TG-C"

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

            self.send_message_with_keyboard(msg=x.title,
                                            chat_id=chat_id,
                                            button_text=["See Image", "Visit Page", "Cancel", "Download"],
                                            button_cb=["echo", "echo", "cancel", "download"],
                                            button_val=[image, x.link, "", x.links[1].href],
                                            arrangement=[3, 1],
                                            reply_to=None
                                            )

    def finance(self, msg, chat_id, message_id, value):
        if value == "":
            self.send_now("Please type the amount after the command. You can press and hold this "
                          "command and type the amount\n /finance", chat=chat_id, reply_to=message_id)
            return

        sql_id = sql_connector.insert('transactions', "amount", str(value), 'finance')
        identifier = "transactions_" + str(sql_id) + "_"

        self.send_message_with_keyboard(msg="Let's fill some missing info",
                                        chat_id=chat_id,
                                        button_text=["Income", "Expense", "Invest", "Delete"],
                                        button_cb=["finance", "finance", "finance", "finance"],
                                        button_val=[identifier + "income",
                                                    identifier + "expense",
                                                    identifier + "invest",
                                                    identifier + "delete"],
                                        arrangement=[3, 1],
                                        reply_to=message_id
                                        )

    def request_tv_show(self, msg, chat_id, message_id, value):
        show = value
        if show == "":
            self.send_now("Please type the name of the tv show after the command. You can press and hold this "
                          "command and type the movie \n /request_tv_show", chat=chat_id)
            return

        request = {show: str(msg['chat']['first_name'])}
        JSONEditor(global_var.requested_show_database).add_level1(request)
        logger.log("TV Show Requested - " + show, source=self.source)
        self.send_now("TV Show Requested - " + show, chat=chat_id, reply_to=message_id)

    def baby_weight(self, msg, chat_id, message_id, value):
        if value == "":
            self.send_now("Please type the weight in kg after the command. You can press and hold this "
                          "command and type the weight \n /baby_weight", chat=chat_id)
            return

        val = {datetime.now().strftime('%Y/%m/$d'): value}
        JSONEditor(global_var.baby_weight_database).add_level1(val)
        logger.log("Baby Weight Added - " + value, source=self.source)
        self.send_now("Baby Weight Added - " + value, chat=chat_id, reply_to=message_id)

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
        identifier = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " "

        value_check_fail = False

        if value != "":
            if "ml" in value:
                value = str(value).replace("ml", "").strip()
            try:
                int(value)
            except ValueError:
                logger.log("Rejected entered feed value", source=self.source)
                value_check_fail = True

        if value == "" or value_check_fail:
            self.send_message_with_keyboard(msg="Need some feeding info",
                                            chat_id=chat_id,
                                            button_text=["30ml", "60ml", "90ml", "120ml", "Cancel"],
                                            button_cb=["feed", "feed", "feed", "feed", "cancel"],
                                            button_val=[identifier + "30",
                                                        identifier + "60",
                                                        identifier + "90",
                                                        identifier + "120",
                                                        ""],
                                            arrangement=[4, 1],
                                            reply_to=message_id
                                            )

        else:
            self.cb_feed(None, None, chat_id, identifier + str(value))

    def baby_diaper(self, msg, chat_id, message_id, value):
        identifier = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " "

        self.send_message_with_keyboard(msg="Need some diaper info",
                                        chat_id=chat_id,
                                        button_text=["Pee", "Poo", "Poo & Pee", "Cancel"],
                                        button_cb=["diaper", "diaper", "diaper", "cancel"],
                                        button_val=[identifier + "pee",
                                                    identifier + "poo",
                                                    identifier + "pp",
                                                    ""],
                                        arrangement=[3, 1],
                                        reply_to=message_id
                                        )

    def baby_feed_history(self, msg, chat_id, message_id, value):
        pic = grapher_category_dictionary(graph_dict=JSONEditor(global_var.baby_feed_database).read(),
                                          x_column="date",
                                          cat_column="source",
                                          data_column="ml",
                                          x_name="Date",
                                          y_name="Amount (ml)",
                                          chart_title="Feed History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_diaper_history(self, msg, chat_id, message_id, value):
        pic = grapher_category_dictionary(graph_dict=JSONEditor(global_var.baby_diaper_database).read(),
                                          x_column="date",
                                          cat_column="what",
                                          data_column="count",
                                          x_name="Date",
                                          y_name="Diapers",
                                          chart_title="Diaper History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_feed_trend(self, msg, chat_id, message_id, value):
        pic = grapher_trend(graph_dict=JSONEditor(global_var.baby_feed_database).read(),
                            t_column="time",
                            cat_column="source",
                            data_column="ml",
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Source",
                            chart_title="Feed Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                            size=True)
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_diaper_trend(self, msg, chat_id, message_id, value):
        pic = grapher_trend(graph_dict=JSONEditor(global_var.baby_diaper_database).read(),
                            t_column="time",
                            cat_column="what",
                            data_column="count",
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Type",
                            chart_title="Diaper Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                            size=True)
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_feed_trend_date(self, msg, chat_id, message_id, value):
        pic = grapher_trend(graph_dict=JSONEditor(global_var.baby_feed_database).read(),
                            t_column="time",
                            cat_column="date",
                            data_column="ml",
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Amount (ml)",
                            chart_title="Feed Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_diaper_trend_date(self, msg, chat_id, message_id, value):
        pic = grapher_trend(graph_dict=JSONEditor(global_var.baby_diaper_database).read(),
                            t_column="time",
                            cat_column="date",
                            data_column="count",
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Diapers",
                            chart_title="Diaper Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_feed_trend_cat(self, msg, chat_id, message_id, value):
        pic = grapher_trend(graph_dict=JSONEditor(global_var.baby_feed_database).read(),
                            t_column="time",
                            cat_column="source",
                            data_column="ml",
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Amount (ml)",
                            chart_title="Feed Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_diaper_trend_cat(self, msg, chat_id, message_id, value):
        pic = grapher_trend(graph_dict=JSONEditor(global_var.baby_diaper_database).read(),
                            t_column="time",
                            cat_column="what",
                            data_column="count",
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Diapers",
                            chart_title="Diaper Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

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

    def cb_feed(self, callback_id, query_id, from_id, value):
        if callback_id is not None:
            self.update_in_line_buttons(callback_id)
            try:
                self.bot.answerCallbackQuery(query_id, text='Got it')
            except telepot.exception.TelegramError:
                pass

        # FORMAT
        # ID <SPACE> ml <SPACE> source

        data = value.split(" ")

        if len(data) == 3:
            self.send_message_with_keyboard(msg="How did you feed " + data[2] + "ml at " + data[1],
                                            chat_id=from_id,
                                            button_text=["Breast", "Express", "Formula", "Cancel"],
                                            button_cb=["feed", "feed", "feed", "cancel"],
                                            button_val=[value + " breast",
                                                        value + " expressed",
                                                        value + " formula",
                                                        ""],
                                            arrangement=[3, 1],
                                            )

        if len(data) == 4:
            self.send_to_group("baby",
                               "resources/baby_milk.png",
                               True,
                               "Baby was fed " + data[2] + "ml on " + data[0] +
                               " at " + data[1] + " with " + data[3] + " milk")
            write_data = {str(data[0]) + " " + str(data[1]): {"date": data[0],
                                                              "time": data[1],
                                                              "ml": data[2],
                                                              "source": data[3]}}
            JSONEditor(global_var.baby_feed_database).add_level1(write_data)

    def cb_diaper(self, callback_id, query_id, from_id, value):
        self.update_in_line_buttons(callback_id)
        try:
            self.bot.answerCallbackQuery(query_id, text='Got it')
        except telepot.exception.TelegramError:
            pass

        data = value.split(" ")
        self.send_to_group("baby",
                           "resources/baby_diaper.png",
                           True,
                           data[2] + " diaper recorded on " + data[0] + " at " + data[1])

        write_data = {str(data[0]) + " " + str(data[1]): {"date": data[0],
                                                          "time": data[1],
                                                          "what": data[2],
                                                          "count": 1}}
        JSONEditor(global_var.baby_diaper_database).add_level1(write_data)


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
