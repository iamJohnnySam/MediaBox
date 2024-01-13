import os
import shutil
import threading
from datetime import datetime

import feedparser
import telepot

import global_var
import logger
import settings
from charts.grapher import grapher_simple_trend, grapher_category, grapher_bar_trend, grapher_weight_trend
from communication.communicator_base import CommunicatorBase
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import SQLConnector
from maintenance.folder_refactor import RefactorFolder
from show import transmission
from show.movie_finder import get_movies_by_name, get_movie_details


# os.environ['_BARD_API_KEY'] = settings.bard


class Communicator(CommunicatorBase):

    def __init__(self, telepot_account):
        super().__init__(telepot_account)
        self.baby_sql = SQLConnector(settings.database_user, settings.database_password, 'baby')
        self.finance_sql = SQLConnector(settings.database_user, settings.database_password, 'transactions')
        self.source = "TG-C"

    def check_shows(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        global_var.check_shows = True
        self.send_now("Request Initiated - TV Show Check",
                      chat=chat_id,
                      reply_to=message_id)

    def check_news(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        global_var.check_news = True
        self.send_now("Request Initiated - News Check",
                      chat=chat_id,
                      reply_to=message_id)

    def check_cctv(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        global_var.check_cctv = True
        self.send_now("Request Initiated - CCTV Check",
                      chat=chat_id,
                      reply_to=message_id)

    def find_movie(self, msg, chat_id, message_id, movie, user_input=False, identifier=None):
        if not self.check_command_value("name of movie", movie, chat_id, message_id):
            return

        self.send_now(f"Searching movie: {movie} for chat_id: {chat_id}.")
        movie_feed = get_movies_by_name(movie)

        for movie_name in movie_feed.entries:
            title, image, link, torrent = get_movie_details(movie_name)

            self.send_message_with_keyboard(msg=title,
                                            chat_id=chat_id,
                                            button_text=["See Image", "Visit Page", "Cancel", "Download"],
                                            button_cb=["echo", "echo", "cancel", "download"],
                                            button_val=[image, link, "", torrent],
                                            arrangement=[3, 1],
                                            reply_to=None
                                            )

    def finance(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        if value == "":
            self.send_now("Please type the amount", chat=chat_id, reply_to=message_id)
            self.get_user_input(chat_id, "finance", None)
            return

        try:
            amount = float(value)
        except ValueError:
            self.send_now("Please type the amount in numbers only", chat=chat_id, reply_to=message_id)
            self.get_user_input(chat_id, "finance", None)
            return

        if user_input and identifier is not None:
            sql_id = identifier
            query = f'UPDATE transaction_lkr SET amount = "{amount}" WHERE transaction_id = "{sql_id}"'
            self.finance_sql.run_sql(query)

        else:
            columns = 'transaction_by, amount'
            val = (chat_id, amount)
            success, sql_id = self.finance_sql.insert('transaction_lkr', columns, val,
                                                      get_id=True,
                                                      id_column='transaction_id')

        prefix = str(sql_id) + ";"

        self.send_message_with_keyboard(msg=f'[{sql_id}] Is LKR {value} an income or expense?',
                                        chat_id=chat_id,
                                        button_text=["Income", "Expense", "Invest", "Delete"],
                                        button_cb=["finance", "finance", "finance", "finance"],
                                        button_val=[prefix + "1;income",
                                                    prefix + "1;expense",
                                                    prefix + "1;invest",
                                                    prefix + "1;delete"],
                                        arrangement=[3, 1],
                                        reply_to=message_id
                                        )

    def sms_bill(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        if not self.check_command_value("sms received from bank", value, chat_id, message_id):
            return
        pass

    def request_tv_show(self, msg, chat_id, message_id, show, user_input=False, identifier=None):
        if not self.check_command_value("name of TV show", show, chat_id, message_id):
            return

        request = {show: str(msg['chat']['first_name'])}
        JSONEditor(global_var.requested_show_database).add_level1(request)
        logger.log("TV Show Requested - " + show, source=self.source)
        self.send_now("TV Show Requested - " + show, chat=chat_id, reply_to=message_id)
        self.send_now("TV Show Requested - " + show)

    def baby_weight(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        if not self.check_command_value("weight of the baby in kg", value, chat_id, message_id, fl=True):
            return
        weight = float(value)

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

    def add_me_to_cctv(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def add_me_to_news(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def remove_me_from_cctv(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def remove_me_from_news(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        self.send_now("Function Not yet implemented",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def list_torrents(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        torrent_list = transmission.list_all()
        self.send_now(str(torrent_list),
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def clean_up_downloads(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        transmission.torrent_complete_sequence()
        self.send_now("Clean-up completed successfully",
                      image=False,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_feed(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        if "ml" in value:
            value = str(value).replace("ml", "").strip()
        if not self.check_command_value("amount consumed in ml", value, chat_id, message_id, tx=False, fl=True):
            return

        identifier = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " "

        if value == "":
            self.send_message_with_keyboard(msg="Need some feeding info",
                                            chat_id=chat_id,
                                            button_text=["30ml", "60ml", "90ml", "Other", "Cancel"],
                                            button_cb=["feed", "feed", "feed", "feed", "cancel"],
                                            button_val=[identifier + "30",
                                                        identifier + "60",
                                                        identifier + "90",
                                                        "GET",
                                                        ""],
                                            arrangement=[4, 1],
                                            reply_to=message_id
                                            )
        else:
            self.cb_feed(None, message_id, chat_id, str(value))

    def baby_diaper(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
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

    def baby_feed_history(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        query = 'SELECT date, source, amount FROM feed ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_category(graph_list=result,
                               x_name="Date",
                               y_name="Amount (ml)",
                               chart_title="Feed History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        today = datetime.now().strftime('%Y-%m-%d')
        query = f'SELECT source, amount FROM feed WHERE date = "{today}"'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        caption = None
        if result is not None:
            calc = {}
            total = 0
            for i in result:
                if i[0] in calc.keys():
                    calc[i[0]] = calc[i[0]] + i[1]
                else:
                    calc[i[0]] = i[1]
                total = total + i[1]

            caption = f'Your baby has had {total}ml of milk today.\nBreakdown:'
            for i in calc.keys():
                caption = caption + f'\n{i} milk = {calc[i]}ml'
            caption = caption + "\nUse /feed to submit a new entry or"\
                                "\nUse /feed_history to see the history."\
                                "\n\n Use /feed_trend to see the trend over time"\
                                "\n Use /feed_trend_today to see what happened today."

        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id,
                      caption=caption)

    def baby_diaper_history(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        query = 'SELECT date, what, count FROM diaper ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_category(graph_list=result,
                               x_name="Date",
                               y_name="Diapers",
                               chart_title="Diaper History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        today = datetime.now().strftime('%Y-%m-%d')
        query = f'SELECT what, count FROM diaper WHERE date = "{today}"'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        caption = None
        if result is not None:
            calc = {}
            total = 0
            for i in result:
                if i[0] in calc.keys():
                    calc[i[0]] = calc[i[0]] + i[1]
                else:
                    calc[i[0]] = i[1]
                total = total + i[1]

            caption = f'Your baby has had {total} nappy changes today.\nBreakdown:'
            for i in calc.keys():
                caption = caption + f'\n{i} = {calc[i]} nappies/diapers'
            caption = caption + "\nUse /diaper to submit a new entry or"\
                                "\nUse /diaper_history to see the history."\
                                "\n\n Use /diaper_trend to see the trend over time"\
                                "\n Use /diaper_trend_today to see what happened today."

        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id,
                      caption=caption)

    def baby_feed_trend(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        query = 'SELECT time, amount, date FROM feed ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (ml)",
                                chart_title="Feed Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_diaper_trend(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        query = 'SELECT time, count, date, what FROM diaper ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (nappies/diapers)",
                                chart_title="Diaper Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id)

    def baby_feed_trend_today(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        query = f'SELECT time, amount, date FROM feed WHERE date = "{datetime.now().strftime("%Y-%m-%d")}" ' \
                f'ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (ml)",
                                chart_title="Feed Trend Today - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)

        query = f'SELECT time, amount, source FROM feed WHERE date = "{datetime.now().strftime("%Y-%m-%d")}" ' \
                f'ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        caption = "Record:"
        for row in result:
            caption = caption + f"\n{row[0]} - {row[1]} - {row[2]}"
        caption = caption + "\nUse /feed to submit a new entry or" \
                            "\nUse /feed_history to see the history." \
                            "\n\n Use /feed_trend to see the trend over time" \
                            "\n Use /feed_trend_today to see what happened today."

        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id,
                      caption= caption)

    def baby_diaper_trend_today(self, msg, chat_id, message_id, value, user_input=False, identifier=None):
        query = f'SELECT time, count, date, what FROM diaper WHERE date = "{datetime.now().strftime("%Y-%m-%d")}" ' \
                f'ORDER BY timestamp'
        result = list(self.baby_sql.run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (nappies/diapers)",
                                chart_title="Diaper Trend Today - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)
        caption = "Record:"
        for row in result:
            caption = caption + f"\n{row[0]} - {row[1]} - {row[3]}"
        caption = caption + "\nUse /diaper to submit a new entry or" \
                            "\nUse /diaper_history to see the history." \
                            "\n\n Use /diaper_trend to see the trend over time" \
                            "\n Use /diaper_trend_today to see what happened today."

        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      reply_to=message_id,
                      caption=caption)

    def baby_weight_trend(self, msg, chat_id, message_id, value, caption=None, user_input=False, identifier=None):
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

        pic = grapher_weight_trend(graph_list=result,
                                   chart_title="Baby Weight Trend WHO - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=chat_id,
                      caption=caption,
                      reply_to=message_id)

    # -------------- PHOTO FUNCTIONS --------------

    def finance_photo(self, callback_id, query_id, from_id, value):
        message_id = self.update_in_line_buttons(callback_id)
        self.bot.answerCallbackQuery(query_id, text='Got it')

        if not os.path.exists(global_var.finance_images):
            os.makedirs(global_var.finance_images)

        columns = 'transaction_by, photo_id'
        val = (from_id, value)
        success, sql_id = self.finance_sql.insert('transaction_lkr', columns, val,
                                                  get_id=True,
                                                  id_column='transaction_id')
        shutil.move(os.path.join(global_var.telepot_image_dump, value),
                    os.path.join(global_var.finance_images, value))
        self.send_now("How much is the amount?", chat=from_id, reply_to=str(message_id))
        self.get_user_input(from_id, "finance", sql_id)

    # -------------- CALLBACK FUNCTIONS --------------

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
        if data[2].lower() == "delete":
            query = f'DELETE FROM transaction_lkr WHERE transaction_id = "{data[0]}"'
            self.finance_sql.run_sql(query, fetch_all=True)
            return

        if data[1] == "1":
            query = f'UPDATE transaction_lkr SET type = "{data[2]}" WHERE transaction_id = "{data[0]}"'
            self.finance_sql.run_sql(query)

            d = datetime.now().strftime("%Y-%m-%d")
            query = f'UPDATE transaction_lkr SET date = "{d}" WHERE transaction_id = "{data[0]}"'
            self.finance_sql.run_sql(query)

            if data[2] == "invest":
                in_out = "income"
            else:
                in_out = data[2]

            query = f'SELECT DISTINCT type FROM categories WHERE in_out = "{in_out}"'
            result = list(self.finance_sql.run_sql(query, fetch_all=True))

            button_text, button_cb, button_value, arrangement = self.keyboard_extractor(data[0], "2", result, 'finance')
            button_text.append("Delete")
            button_cb.append("finance")
            button_value.append(f'{data[0]};2;Delete')
            arrangement.append(1)

            self.send_message_with_keyboard(msg=f'[{data[0]}] What type of {data[2]} was it?',
                                            chat_id=from_id,
                                            button_text=button_text,
                                            button_cb=button_cb,
                                            button_val=button_value,
                                            arrangement=arrangement,
                                            reply_to=message_id
                                            )
        elif data[1] == "2":
            query = f'SELECT DISTINCT category FROM categories WHERE type = "{data[2]}"'
            result = list(self.finance_sql.run_sql(query, fetch_all=True))

            button_text, button_cb, button_value, arrangement = self.keyboard_extractor(data[0], "3", result, 'finance')
            button_text.append("Delete")
            button_cb.append("finance")
            button_value.append(f'{data[0]};3;Delete')
            arrangement.append(1)

            self.send_message_with_keyboard(msg=f'[{data[0]}] What is the category of {data[2]}',
                                            chat_id=from_id,
                                            button_text=button_text,
                                            button_cb=button_cb,
                                            button_val=button_value,
                                            arrangement=arrangement,
                                            reply_to=message_id
                                            )
        elif data[1] == "3":
            query = f'SELECT category_id FROM categories WHERE category = "{data[2]}"'
            cat_id = list(self.finance_sql.run_sql(query))[0]
            query = f'UPDATE transaction_lkr SET category_id = "{cat_id}" WHERE transaction_id = "{data[0]}"'
            self.finance_sql.run_sql(query, fetch_all=True)
            logger.log(f'Updated Transaction - {data[0]}')
            self.send_now(f'[{data[0]}] Transaction successfully updated', chat=from_id)

    def cb_feed(self, callback_id, query_id, from_id, value):
        if callback_id is not None:
            message_id = self.update_in_line_buttons(callback_id)
            try:
                self.bot.answerCallbackQuery(query_id, text='Got it')
            except telepot.exception.TelegramError:
                pass
            if value == "GET":
                self.check_command_value("amount consumed in ml", "", from_id, message_id, tx=True, fl=False)

        # FORMAT
        # ID <SPACE> ml <SPACE> source

        if callback_id is None:
            if not self.check_command_value("amount consumed in ml", value, from_id, query_id, tx=True, fl=False):
                return
            value = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + value

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
                               f'\U0001F37C '
                               f'\nBaby was fed {data[2]}ml on {data[0]} at {data[1]} with {data[3]}  milk. '
                               f'\nFor today your baby has had ' + "{:10.1f}".format(day_total) + "ml of milk" +
                               "\nUse /feed to submit a new entry or"
                               "\nUse /feed_history to see the history."
                               "\n\n Use /feed_trend to see the trend over time"
                               "\n Use /feed_trend_today to see what happened today.")

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
                           ". \nYour baby has had " + str(day_total) + " nappy/diaper changes today\n" +
                           "Use /diaper to submit a new entry or"
                           "\nUse /diaper_history to see the history."
                           "\n\n Use /diaper_trend to see the trend over time or "
                           "\n Use /diaper_trend_today to see what happened today.")


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
