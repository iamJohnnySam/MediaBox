import os
import shutil
import threading
from datetime import datetime

import telepot

import global_var
import logger
from charts.grapher import grapher_simple_trend, grapher_category, grapher_bar_trend, grapher_weight_trend
from communication.communicator_base import CommunicatorBase
from communication.message import Message
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import sql_databases
from show import transmission
from show.movie_finder import get_movies_by_name, get_movie_details


class Communicator(CommunicatorBase):

    def __init__(self, telepot_account):
        super().__init__(telepot_account)

    def check_shows(self, msg: Message):
        global_var.check_shows = True
        self.send_now("Request Initiated - TV Show Check", msg=msg)

    def check_news(self, msg: Message):
        global_var.check_news = True
        self.send_now("Request Initiated - News Check", msg=msg)

    def check_cctv(self, msg: Message):
        global_var.check_cctv = True
        self.send_now("Request Initiated - CCTV Check", msg=msg)

    def subscribe_news(self, msg: Message):
        news = JSONEditor(global_var.news_sources).read()
        news_channels = []
        prev_channel = ""
        for channel in news.keys():
            if type(news[channel]) is bool:
                if len(news_channels) != 0:
                    btn_text, btn_cb, btn_value, arr = self.keyboard_extractor(msg.chat_id, "", news_channels,
                                                                               'subs_news',
                                                                               sql_result=False, command_only=True)
                    self.send_with_keyboard(msg=prev_channel, chat_id=msg.chat_id,
                                            button_text=btn_text, button_cb=btn_cb, button_val=btn_value,
                                            arrangement=arr)
                prev_channel = channel
                news_channels = []
            else:
                news_channels.append(channel)

    def find_movie(self, msg: Message):
        if not self.check_command_value(msg, inquiry="name of movie"):
            return

        self.send_now(f"Searching movie: {msg.value}.", msg=msg)
        movie_feed = get_movies_by_name(msg.value)

        for movie_name in movie_feed.entries:
            title, image, link, torrent = get_movie_details(movie_name)

            self.send_with_keyboard(send_string=title,
                                    msg=msg,
                                    photo=image,
                                    button_text=["Visit Page", "Download"],
                                    button_cb=["echo", "download"],
                                    button_val=[link, torrent],
                                    arrangement=[2])

    def finance(self, msg: Message):
        if msg.value == "":
            self.send_now("Please type the amount", chat=msg.chat_id, reply_to=msg.message_id)
            self.get_user_input(msg.chat_id, "finance", None)
            return

        try:
            amount = float(msg.value)
        except ValueError:
            self.send_now("Please type the amount in numbers only", chat=msg.chat_id, reply_to=msg.message_id)
            self.get_user_input(msg.chat_id, "finance", None)
            return

        if user_input and identifier is not None:
            sql_id = identifier
            query = f'UPDATE transaction_lkr SET amount = "{amount}" WHERE transaction_id = "{sql_id}"'
            sql_databases["finance"].run_sql(query)

        else:
            columns = 'transaction_by, amount'
            val = (msg.chat_id, amount)
            success, sql_id = sql_databases["finance"].insert('transaction_lkr', columns, val,
                                                              get_id=True,
                                                              id_column='transaction_id')

        prefix = str(sql_id) + ";"

        self.send_with_keyboard(msg=f'[{sql_id}] Is LKR {msg.value} an income or expense?',
                                chat_id=msg.chat_id,
                                button_text=["Income", "Expense", "Invest", "Delete"],
                                button_cb=["finance", "finance", "finance", "finance"],
                                button_val=[prefix + "1;income",
                                                    prefix + "1;expense",
                                                    prefix + "1;invest",
                                                    prefix + "1;delete"],
                                arrangement=[3, 1],
                                reply_to=msg.message_id
                                )

    def sms_bill(self, msg: Message):
        if not self.check_command_value(msg, inquiry="sms received from bank"):
            return
        pass

    def request_tv_show(self, msg: Message):
        if not self.check_command_value(msg, inquiry="name of TV show"):
            return

        sql_databases["entertainment"].insert("requested_shows",
                                              "name, requested_by, requested_id",
                                              (msg.value, msg.f_name, msg.chat_id))
        logger.log("TV Show Requested - " + msg.value)
        self.send_now("TV Show Requested - " + msg.value, chat=msg.chat_id, reply_to=msg.message_id)
        self.send_now("TV Show Requested - " + msg.value)

    def baby_weight(self, msg: Message):
        if not self.check_command_value(msg, replace="kg", inquiry="weight of baby in kg", check_float=True):
            return
        weight = float(msg.value)

        key = datetime.now().strftime('%Y/%m/%d')

        query = 'SELECT date, weight FROM weight ORDER BY weight_id DESC LIMIT 1;'
        last_entry = sql_databases["baby"].run_sql(query=query)

        columns = "date, weight, added_by"
        val = (key, weight, str(msg.chat_id))
        sql_databases["baby"].insert('weight', columns, val)

        send_string = "\U0001F6BC \U0001F3C6 \n" + \
                      "Baby Weight Added - " + msg.value + "kg. \nThat's a weight gain of " + \
                      "{:10.2f}".format(weight - last_entry[1]) + "kg since " + str(last_entry[0]) + "."

        logger.log(send_string)
        self.baby_weight_trend(msg, caption=send_string)

    def add_me_to_cctv(self, msg: Message):
        self.manage_chat_group("cctv", msg.chat_id)
        self.send_now("Done", chat=msg.chat_id, reply_to=msg.message_id)

    def add_me_to_news(self, msg: Message):
        self.manage_chat_group("news", msg.chat_id)
        self.send_now("Done", chat=msg.chat_id, reply_to=msg.message_id)

    def add_me_to_baby(self, msg: Message):
        self.manage_chat_group("baby", msg.chat_id)
        self.send_now("Done", chat=msg.chat_id, reply_to=msg.message_id)

    def remove_me_from_cctv(self, msg: Message):
        self.manage_chat_group("cctv", msg.chat_id, add=False, remove=True)
        self.send_now("Done", chat=msg.chat_id, reply_to=msg.message_id)

    def remove_me_from_news(self, msg: Message):
        self.manage_chat_group("news", msg.chat_id, add=False, remove=True)
        self.send_now("Done", chat=msg.chat_id, reply_to=msg.message_id)

    def remove_me_from_baby(self, msg: Message):
        self.manage_chat_group("baby", msg.chat_id, add=False, remove=True)
        self.send_now("Done", chat=msg.chat_id, reply_to=msg.message_id)

    def list_torrents(self, msg: Message):
        torrent_list = transmission.list_all()
        self.send_now(str(torrent_list),
                      chat=msg.chat_id,
                      reply_to=msg.message_id)

    def clean_up_downloads(self, msg: Message):
        transmission.torrent_complete_sequence()
        self.send_now("Clean-up completed successfully",
                      chat=msg.chat_id,
                      reply_to=msg.message_id)

    def baby_feed(self, msg: Message):
        if not self.check_command_value(msg, replace="ml", check_float=True):
            return

        identifier = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " "

        if msg.value == "":
            self.send_with_keyboard(msg="Need some feeding info",
                                    chat_id=msg.chat_id,
                                    button_text=["30ml", "60ml", "90ml", "Other", "Cancel"],
                                    button_cb=["feed", "feed", "feed", "feed", "cancel"],
                                    button_val=[identifier + "30",
                                                        identifier + "60",
                                                        identifier + "90",
                                                        "GET",
                                                        ""],
                                    arrangement=[4, 1],
                                    reply_to=msg.message_id
                                    )
        else:
            self.cb_feed(None, msg.message_id, msg.chat_id, str(msg.value))

    def mom_pump(self, msg: Message):
        if not self.check_command_value(msg, replace="ml", check_float=True):
            return

        identifier = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " "

        if msg.value == "":
            self.send_with_keyboard(msg="Need some pumping info",
                                    chat_id=msg.chat_id,
                                    button_text=["10ml", "20ml", "30ml", "40ml", "Other", "Cancel"],
                                    button_cb=["pump", "pump", "pump", "pump", "pump", "cancel"],
                                    button_val=[identifier + "10",
                                                        identifier + "20",
                                                        identifier + "30",
                                                        identifier + "40",
                                                        "GET",
                                                        ""],
                                    arrangement=[4, 2],
                                    reply_to=msg.message_id
                                    )
        else:
            self.cb_pump(None, msg.message_id, msg.chat_id, str(msg.value))

    def baby_diaper(self, msg: Message):
        identifier = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " "

        self.send_with_keyboard(msg="Need some diaper info",
                                chat_id=msg.chat_id,
                                button_text=["Pee", "Poo", "Poo & Pee", "Cancel"],
                                button_cb=["diaper", "diaper", "diaper", "cancel"],
                                button_val=[identifier + "pee",
                                                    identifier + "poo",
                                                    identifier + "pp",
                                                    ""],
                                arrangement=[3, 1],
                                reply_to=msg.message_id
                                )

    def baby_feed_history(self, msg: Message):
        query = 'SELECT date, source, amount FROM feed ORDER BY timestamp'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))

        pic = grapher_category(graph_list=result,
                               x_name="Date",
                               y_name="Amount (ml)",
                               chart_title="Feed History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        today = datetime.now().strftime('%Y-%m-%d')
        query = f'SELECT source, amount FROM feed WHERE date = "{today}"'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))

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
            caption = caption + "\nUse /feed to submit a new entry or" \
                                "\nUse /feed_history to see the history." \
                                "\n\nUse /feed_trend to see the trend over time" \
                                "\nUse /feed_trend_today to see what happened today."

        self.send_now(pic,
                      image=True,
                      chat=msg.chat_id,
                      reply_to=msg.message_id,
                      caption=caption)

    def baby_diaper_history(self, msg: Message):
        query = 'SELECT date, what, count FROM diaper ORDER BY timestamp'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))

        pic = grapher_category(graph_list=result,
                               x_name="Date",
                               y_name="Diapers",
                               chart_title="Diaper History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        today = datetime.now().strftime('%Y-%m-%d')
        query = f'SELECT what, count FROM diaper WHERE date = "{today}"'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))

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
            caption = caption + "\nUse /diaper to submit a new entry or" \
                                "\nUse /diaper_history to see the history." \
                                "\n\nUse /diaper_trend to see the trend over time" \
                                "\nUse /diaper_trend_today to see what happened today."

        self.send_now(pic,
                      image=True,
                      chat=msg.chat_id,
                      reply_to=msg.message_id,
                      caption=caption)

    def baby_feed_trend(self, msg: Message):
        query = 'SELECT time, amount, date FROM feed ORDER BY timestamp'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (ml)",
                                chart_title="Feed Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)
        self.send_now(pic,
                      image=True,
                      chat=msg.chat_id,
                      reply_to=msg.message_id)

    def baby_diaper_trend(self, msg: Message):
        query = 'SELECT time, count, date, what FROM diaper ORDER BY timestamp'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (nappies/diapers)",
                                chart_title="Diaper Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)
        self.send_now(pic,
                      image=True,
                      chat=msg.chat_id,
                      reply_to=msg.message_id)

    def baby_feed_trend_today(self, msg: Message):
        query = f'SELECT time, amount, date FROM feed WHERE date = "{datetime.now().strftime("%Y-%m-%d")}" ' \
                f'ORDER BY timestamp'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (ml)",
                                chart_title="Feed Trend Today - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)

        query = f'SELECT time, amount, source FROM feed WHERE date = "{datetime.now().strftime("%Y-%m-%d")}" ' \
                f'ORDER BY timestamp'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))

        caption = "Record:"
        for row in result:
            caption = caption + f"\n{row[0]} - {row[1]} - {row[2]}"
        caption = caption + "\nUse /feed to submit a new entry or" \
                            "\nUse /feed_history to see the history." \
                            "\n\nUse /feed_trend to see the trend over time" \
                            "\nUse /feed_trend_today to see what happened today."

        self.send_now(pic,
                      image=True,
                      chat=msg.chat_id,
                      reply_to=msg.message_id,
                      caption=caption)

    def baby_diaper_trend_today(self, msg: Message):
        query = f'SELECT time, count, date, what FROM diaper WHERE date = "{datetime.now().strftime("%Y-%m-%d")}" ' \
                f'ORDER BY timestamp'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))

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
                            "\n\nUse /diaper_trend to see the trend over time" \
                            "\nUse /diaper_trend_today to see what happened today."

        self.send_now(pic,
                      image=True,
                      chat=msg.chat_id,
                      reply_to=msg.message_id,
                      caption=caption)

    def baby_weight_trend(self, msg: Message, caption=None):
        query = 'SELECT date, weight FROM weight ORDER BY timestamp'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))

        if caption is None:
            caption = "\U0001F37C \U0001F3C6 \nBaby Weight trend. Add new weight using /weight command"

        pic = grapher_simple_trend(graph_list=result,
                                   x_name="Date",
                                   y_name="Weight (kg)",
                                   chart_title="Baby Weight Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=msg.chat_id,
                      caption=caption,
                      reply_to=msg.message_id)

        pic = grapher_weight_trend(graph_list=result,
                                   chart_title="Baby Weight Trend WHO - " + datetime.now().strftime('%Y-%m-%d %H:%M'))
        self.send_now(pic,
                      image=True,
                      chat=msg.chat_id,
                      caption=caption,
                      reply_to=msg.message_id)

    # -------------- PHOTO FUNCTIONS --------------

    def finance_photo(self, callback_id, query_id, from_id, value):
        message_id = self.update_in_line_buttons(callback_id)
        self.bot.answerCallbackQuery(query_id, text='Got it')

        if not os.path.exists(global_var.finance_images):
            os.makedirs(global_var.finance_images)

        columns = 'transaction_by, photo_id'
        val = (from_id, value)
        success, sql_id = sql_databases["finance"].insert('transaction_lkr', columns, val,
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
            sql_databases["finance"].run_sql(query, fetch_all=True)
            return

        if data[1] == "1":
            query = f'UPDATE transaction_lkr SET type = "{data[2]}" WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query)

            d = datetime.now().strftime("%Y-%m-%d")
            query = f'UPDATE transaction_lkr SET date = "{d}" WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query)

            if data[2] == "invest":
                in_out = "income"
            else:
                in_out = data[2]

            query = f'SELECT DISTINCT type FROM categories WHERE in_out = "{in_out}"'
            result = list(sql_databases["finance"].run_sql(query, fetch_all=True))

            button_text, button_cb, button_value, arrangement = self.keyboard_extractor(data[0], "2", result, 'finance')
            button_text.append("Delete")
            button_cb.append("finance")
            button_value.append(f'{data[0]};2;Delete')
            arrangement.append(1)

            self.send_with_keyboard(msg=f'[{data[0]}] What type of {data[2]} was it?',
                                    chat_id=from_id,
                                    button_text=button_text,
                                    button_cb=button_cb,
                                    button_val=button_value,
                                    arrangement=arrangement,
                                    reply_to=message_id
                                    )
        elif data[1] == "2":
            query = f'SELECT DISTINCT category FROM categories WHERE type = "{data[2]}"'
            result = list(sql_databases["finance"].run_sql(query, fetch_all=True))

            button_text, button_cb, button_value, arrangement = self.keyboard_extractor(data[0], "3", result, 'finance')
            button_text.append("Delete")
            button_cb.append("finance")
            button_value.append(f'{data[0]};3;Delete')
            arrangement.append(1)

            self.send_with_keyboard(msg=f'[{data[0]}] What is the category of {data[2]}',
                                    chat_id=from_id,
                                    button_text=button_text,
                                    button_cb=button_cb,
                                    button_val=button_value,
                                    arrangement=arrangement,
                                    reply_to=message_id
                                    )
        elif data[1] == "3":
            query = f'SELECT category_id FROM categories WHERE category = "{data[2]}"'
            cat_id = list(sql_databases["finance"].run_sql(query))[0]
            query = f'UPDATE transaction_lkr SET category_id = "{cat_id}" WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query, fetch_all=True)
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
            self.send_with_keyboard(msg="How did you feed " + data[2] + "ml at " + data[1],
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
            result = list(sql_databases["baby"].run_sql(query, fetch_all=1))
            for val in result:
                day_total = day_total + val[0]
            day_total = day_total + float(data[2])

            columns = "date, time, amount, source, added_by"
            val = (data[0], data[1], float(data[2]), data[3], str(from_id))
            sql_databases["baby"].insert('feed', columns, val)

            self.send_to_group("baby",
                               f'\U0001F37C '
                               f'\nBaby was fed {data[2]}ml on {data[0]} at {data[1]} with {data[3]}  milk. '
                               f'\nFor today your baby has had ' + "{:10.1f}".format(day_total).strip() + "ml of milk" +
                               "\nUse /feed to submit a new entry or"
                               "\nUse /feed_history to see the history."
                               "\n\nUse /feed_trend to see the trend over time"
                               "\nUse /feed_trend_today to see what happened today.")

    def cb_pump(self, callback_id, query_id, from_id, value):
        if callback_id is not None:
            message_id = self.update_in_line_buttons(callback_id)
            try:
                self.bot.answerCallbackQuery(query_id, text='Got it')
            except telepot.exception.TelegramError:
                pass
            if value == "GET":
                self.check_command_value("amount pumped in ml", "", from_id, message_id, tx=True, fl=False)

        # FORMAT
        # ID <SPACE> ml <SPACE> source

        if callback_id is None:
            if not self.check_command_value("amount pumped in ml", value, from_id, query_id, tx=True, fl=False):
                return
            value = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + value

        data = value.split(" ")

        if len(data) == 3:
            self.send_with_keyboard(msg="From which breast did you pump " + data[2] + "ml at " + data[1],
                                    chat_id=from_id,
                                    button_text=["Left", "Right", "Both", "Cancel"],
                                    button_cb=["pump", "pump", "pump", "cancel"],
                                    button_val=[value + " left",
                                                        value + " right",
                                                        value + " both",
                                                        ""],
                                    arrangement=[3, 1],
                                    )

        if len(data) == 4:
            day_total = 0.0
            query = f'SELECT amount FROM pump WHERE date = "{data[0]}"'
            result = list(sql_databases["baby"].run_sql(query, fetch_all=1))
            for val in result:
                day_total = day_total + val[0]
            day_total = day_total + float(data[2])

            columns = "date, time, amount, breast, user_id"
            val = (data[0], data[1], float(data[2]), data[3], str(from_id))
            sql_databases["baby"].insert('pump', columns, val)

            self.send_now(f'\U0001F37C\nYou pumped {data[2]}ml on {data[0]} at {data[1]} from {data[3]} boob.',
                          chat=from_id)

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
            sql_databases["baby"].insert('diaper', columns, val)
            val = (data[0], data[1], "pee", 1, str(from_id))
            sql_databases["baby"].insert('diaper', columns, val)
            emoji = '\U0001F6BC \U0001F4A6 \U0001F4A9 '
        else:
            val = (data[0], data[1], data[2], 1, str(from_id))
            sql_databases["baby"].insert('diaper', columns, val)
            if data[2] == "pee":
                emoji = '\U0001F6BC \U0001F4A6 '
            else:
                emoji = '\U0001F6BC \U0001F4A9 '

        day_total = 0
        query = f'SELECT count FROM diaper WHERE date = "{data[0]}"'
        result = list(sql_databases["baby"].run_sql(query, fetch_all=1))
        for val in result:
            day_total = day_total + val[0]

        self.send_to_group("baby",
                           emoji + "\n" +
                           data[2] + " diaper recorded on " + data[0] + " at " + data[1] +
                           ".\nYour baby has had " + str(day_total) + " nappy/diaper changes today.\n" +
                           "Use /diaper to submit a new entry or"
                           "\nUse /diaper_history to see the history."
                           "\n\nUse /diaper_trend to see the trend over time or "
                           "\nUse /diaper_trend_today to see what happened today.")

    def cb_subs_news(self, callback_id, query_id, from_id, value):
        data = value.split(";")

        if not sql_databases["administration"].exists(self.database_groups,
                                                      f"group_name = 'news_{data[1]}' AND chat_id = '{from_id}'") == 0:
            self.manage_chat_group(f'news_{data[1]}', from_id, add=False, remove=True)
            reply_text = f"You are Unsubscribed from {data[1]}."

        else:
            self.manage_chat_group(f'news_{data[1]}', from_id)
            reply_text = f"You are now Subscribed to {data[1]}."

        try:
            self.bot.answerCallbackQuery(query_id, text=reply_text)
        except telepot.exception.TelegramError:
            pass


telepot_lock = threading.Lock()

telepot_channels = {}
for account in JSONEditor('communication/telepot_accounts.json').read().keys():
    telepot_channels[account] = Communicator(account)


def send_message(telepot_account, chat_id, msg, image=False, keyboard=None, reply_to=None, caption=""):
    telepot_lock.acquire()
    msg_id = telepot_channels[telepot_account].send_now(msg, image, chat_id,
                                                        caption=caption,
                                                        reply_to=reply_to,
                                                        keyboard=keyboard)
    telepot_lock.release()
    return msg_id


def send_to_master(telepot_account, msg, image=False, keyboard=None, reply_to=None, caption=""):
    telepot_lock.acquire()
    msg_id = telepot_channels[telepot_account].send_now(msg, image,
                                                        caption=caption,
                                                        reply_to=reply_to,
                                                        keyboard=keyboard)
    telepot_lock.release()
    return msg_id


def send_to_group(telepot_account, msg, group, image=False, caption=""):
    telepot_lock.acquire()
    telepot_channels[telepot_account].send_to_group(group, msg, image,
                                                    caption=caption)
    telepot_lock.release()
