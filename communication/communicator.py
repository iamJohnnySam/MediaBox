import threading
import feedparser
import telepot

import logger
from datetime import datetime
import global_var
import settings
from charts.grapher import grapher_trend, grapher_simple_trend, grapher_category

from communication.communicator_base import CommunicatorBase
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import SQLConnector
from show import transmission


# os.environ['_BARD_API_KEY'] = settings.bard


class Communicator(CommunicatorBase):

    def __init__(self, telepot_account):
        super().__init__(telepot_account)
        self.baby_sql = SQLConnector(settings.database_user, settings.database_password, 'baby')
        self.finance_sql = SQLConnector(settings.database_user, settings.database_password, 'transactions')
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

        try:
            amount = float(value)
        except ValueError:
            self.send_now("Please type the amount after the command. You can press and hold this "
                          "command and type the amount\n /finance", chat=chat_id, reply_to=message_id)
            return

        columns = 'transaction_by, amount'
        val = (chat_id, amount)
        success, sql_id = self.finance_sql.insert('transaction_lkr', columns, val,
                                                  get_id=True,
                                                  id_column='transaction_id')
        identifier = str(sql_id) + ";"

        self.send_message_with_keyboard(msg=f'Is LKR {value} an income or expense?',
                                        chat_id=chat_id,
                                        button_text=["Income", "Expense", "Invest", "Delete"],
                                        button_cb=["finance", "finance", "finance", "finance"],
                                        button_val=[identifier + "1;income",
                                                    identifier + "1;expense",
                                                    identifier + "1;invest",
                                                    identifier + "1;delete"],
                                        arrangement=[3, 1],
                                        reply_to=message_id
                                        )

    def request_tv_show(self, msg, chat_id, message_id, value):
        show = value
        if show == "":
            self.send_now("Please type the name of the tv show after the command. You can press and hold this "
                          "command and type the movie \n /request_tv_show", chat=chat_id, reply_to=message_id)
            return

        request = {show: str(msg['chat']['first_name'])}
        JSONEditor(global_var.requested_show_database).add_level1(request)
        logger.log("TV Show Requested - " + show, source=self.source)
        self.send_now("TV Show Requested - " + show, chat=chat_id, reply_to=message_id)

    def baby_weight(self, msg, chat_id, message_id, value):
        if value == "":
            self.send_now("Please type the weight in kg after the command. You can press and hold this "
                          "command and type the weight \n /baby_weight", chat=chat_id, reply_to=message_id)
            return

        try:
            weight = float(value)
        except ValueError:
            self.send_now("Please type the weight in kg. Please enter the number only",
                          chat=chat_id, reply_to=message_id)
            return

        key = datetime.now().strftime('%Y/%m/%d')

        query = 'SELECT date, weight FROM weight ORDER BY weight_id DESC LIMIT 1;'
        last_entry = self.baby_sql.run_sql(query=query)

        columns = "date, weight, added_by"
        val = (key, weight, str(chat_id))
        self.baby_sql.insert('weight', columns, val)

        send_string = "\U0001F6BC \U0001F3C6 \n" + \
                      "Baby Weight Added - " + value + "kg. \nThat's a weight gain of " + \
                      "{:10.2f}".format(weight - last_entry[1]) + "kg since " + str(last_entry[0]) + "."

        logger.log(send_string, source=self.source)
        self.baby_weight_trend(msg, chat_id, message_id, value, caption=send_string)

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
        query = 'SELECT date, source, amount FROM feed ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_category(graph_list=result,
                               x_name="Date",
                               y_name="Amount (ml)",
                               chart_title="Feed History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_diaper_history(self, msg, chat_id, message_id, value):
        query = 'SELECT date, what, count FROM diaper ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_category(graph_list=result,
                               x_name="Date",
                               y_name="Diapers",
                               chart_title="Diaper History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_feed_trend(self, msg, chat_id, message_id, value):
        query = 'SELECT time, source, amount FROM feed ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_trend(graph_list=result,
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Source",
                            chart_title="Feed Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                            size=True)
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_diaper_trend(self, msg, chat_id, message_id, value):
        query = 'SELECT time, what, count FROM diaper ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_trend(graph_list=result,
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Type",
                            chart_title="Diaper Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                            size=True)
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_feed_trend_date(self, msg, chat_id, message_id, value):
        query = 'SELECT time, date, amount FROM feed ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_trend(graph_list=result,
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Amount (ml)",
                            chart_title="Feed Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_diaper_trend_date(self, msg, chat_id, message_id, value):
        query = 'SELECT time, date, count FROM diaper ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_trend(graph_list=result,
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Diapers",
                            chart_title="Diaper Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_feed_trend_cat(self, msg, chat_id, message_id, value):
        query = 'SELECT time, source, amount FROM feed ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_trend(graph_list=result,
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Amount (ml)",
                            chart_title="Feed Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_diaper_trend_cat(self, msg, chat_id, message_id, value):
        query = 'SELECT time, what, count FROM diaper ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_trend(graph_list=result,
                            x_name="Time of Day (round to nearest hour)",
                            y_name="Number of Diapers",
                            chart_title="Diaper Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_weight_trend(self, msg, chat_id, message_id, value, caption=None):
        query = 'SELECT date, weight FROM weight ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        if caption is None:
            caption = "\U0001F37C \U0001F3C6 \nBaby Weight trend. Add new weight using /weight command"

        pic = grapher_simple_trend(graph_list=result,
                                   x_name="Date",
                                   y_name="Weight (kg)",
                                   chart_title="Baby Weight Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      caption=caption,
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
        message_id = self.update_in_line_buttons(callback_id)
        self.bot.answerCallbackQuery(query_id, text='Got it')

        data = value.split(";")
        if data[2] == "Delete":
            query = f'DELETE FROM transaction_lkr WHERE transaction_id = "{data[0]}"'
            self.finance_sql.run_sql(query, fetch_all=True)

        if data[1] == "1":
            query = f'UPDATE transaction_lkr SET type = "{data[2]}" WHERE transaction_id = "{data[0]}"'
            self.finance_sql.run_sql(query, fetch_all=True)

            if data[2] == "invest":
                in_out = "income"
            else:
                in_out = data[2]

            query = f'SELECT DISTINCT type FROM categories WHERE in_out = "{in_out}"'
            result = list(self.finance_sql.run_sql(query, fetch_all=True))

            button_text, button_cb, button_value, arrangement = self.keyboard_extractor(data[0], "2", result)
            button_text.append("Delete")
            button_cb.append("finance")
            button_value.append(f'{data[0]};2;Delete')
            arrangement.append(1)

            self.send_message_with_keyboard(msg=f'What type of {data[2]} was it?',
                                            chat_id=from_id,
                                            button_text=button_text,
                                            button_cb=button_cb,
                                            button_val=button_value,
                                            arrangement=arrangement,
                                            reply_to=str(message_id)
                                            )
        elif data[1] == "2":
            query = f'SELECT DISTINCT category FROM categories WHERE type = "{data[2]}"'
            result = list(self.finance_sql.run_sql(query, fetch_all=True))

            button_text, button_cb, button_value, arrangement = self.keyboard_extractor(data[0], "3", result)
            button_text.append("Delete")
            button_cb.append("finance")
            button_value.append(f'{data[0]};3;Delete')
            arrangement.append(1)

            self.send_message_with_keyboard(msg=f'What is the category of {data[2]}',
                                            chat_id=from_id,
                                            button_text=button_text,
                                            button_cb=button_cb,
                                            button_val=button_value,
                                            arrangement=arrangement,
                                            reply_to=str(message_id)
                                            )
        elif data[1] == "3":
            query = f'SELECT category_id FROM categories WHERE category = "{data[2]}"'
            cat_id = list(self.finance_sql.run_sql(query))[0]
            query = f'UPDATE transaction_lkr SET category_id = "{cat_id}" WHERE transaction_id = "{data[0]}"'
            self.finance_sql.run_sql(query, fetch_all=True)
            logger.log(f'Updated Transaction - {data[0]}')

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
            day_total = 0.0
            query = f'SELECT amount FROM feed WHERE date = "{data[0]}"'
            result = list(self.baby_sql.run_sql(query, fetch_all=1))
            for val in result:
                day_total = day_total + val[0]
            day_total = day_total + float(data[2])

            columns = "date, time, amount, source, added_by"
            val = (data[0], data[1], float(data[2]), data[3], str(from_id))
            self.baby_sql.insert('feed', columns, val)

            self.send_to_group("baby",
                               "\U0001F37C \n" +
                               "Baby was fed " + data[2] + "ml on " + data[0] +
                               " at " + data[1] + " with " + data[3] +
                               " milk. \nFor today your baby has had " + "{:10.1f}".format(day_total) +
                               "ml of milk\nUse /feed to submit a new entry or\n" +
                               "Use /feed_history to see the history.")

    def cb_diaper(self, callback_id, query_id, from_id, value):
        self.update_in_line_buttons(callback_id)
        try:
            self.bot.answerCallbackQuery(query_id, text='Got it')
        except telepot.exception.TelegramError:
            pass

        data = value.split(" ")

        columns = "date, time, what, count, added_by"

        if data[2] == "pp":
            val = (data[0], data[1], "poo", 1, str(from_id))
            self.baby_sql.insert('diaper', columns, val)
            val = (data[0], data[1], "pee", 1, str(from_id))
            self.baby_sql.insert('diaper', columns, val)
            emoji = '\U0001F6BC \U0001F4A6 \U0001F4A9 '
        else:
            val = (data[0], data[1], data[2], 1, str(from_id))
            self.baby_sql.insert('diaper', columns, val)
            if data[2] == "pee":
                emoji = '\U0001F6BC \U0001F4A6 '
            else:
                emoji = '\U0001F6BC \U0001F4A9 '

        day_total = 0
        query = f'SELECT count FROM diaper WHERE date = "{data[0]}"'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))
        for val in result:
            day_total = day_total + val[0]

        self.send_to_group("baby",
                           emoji + "\n" +
                           data[2] + " diaper recorded on " + data[0] + " at " + data[1] +
                           ". \nYour baby has had " + str(day_total) + "nappy/diaper changes today\n" +
                           "Use /diaper to submit a new entry or\n" +
                           "Use /diaper_history to see the history.")


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
