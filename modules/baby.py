from datetime import datetime

from tools import logger
from tools.grapher import grapher_simple_trend, grapher_weight_trend, grapher_category, grapher_bar_trend
from tools.custom_exceptions import *
from brains.job import Job
from database_manager.sql_connector import sql_databases
from modules.base_module import Module


class Baby(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        self._db = sql_databases["baby"]
        logger.log(self._job.job_id, f"Baby Module Created")
        self._group = "baby"

    def feed(self):
        amount_list = ["30ml", "60ml", "90ml", "120ml"]
        success, amount = self.check_value(index=0, replace_str="ml", check_float=True, option_list=amount_list,
                                           description="amount consumed")
        if not success:
            return
        source_types = ["Breast", "Express", "Formula"]
        success, source = self.check_value(index=1, check_list=source_types, default="Formula",
                                           description="source")
        if not success:
            return
        success, date = self.check_value(index=2, check_date=True, default=datetime.today().strftime('%Y-%m-%d'),
                                         description="date")
        if not success:
            return
        success, time = self.check_value(index=3, check_time=True, default=datetime.now().strftime('%H:%M:%S'),
                                         description="time")
        if not success:
            return

        day_total = 0.0
        query = f'SELECT amount FROM feed WHERE date = "{date}"'
        result = list(self._db.run_sql(query, fetch_all=1))
        for val in result:
            day_total = day_total + val[0]
        day_total = day_total + float(amount)

        columns = "date, time, amount, source, added_by"
        val = (date, time, float(amount), source, str(self._job.chat_id))
        self._db.insert('feed', columns, val)

        self.send_message(message=f'\U0001F37C\nBaby was fed {amount}ml on {date} at {time} with {source}  milk. '
                                  f'\nYour baby has had ' + "{:10.1f}".format(day_total).strip() +
                                  "ml of milk\nUse /feed to submit a new entry",
                          group=self._group)
        self._job.complete()

    def pump(self):
        amount_list = ["10ml", "20ml", "30ml", "40ml"]
        success, amount = self.check_value(index=0, replace_str="ml", check_float=True, option_list=amount_list)
        if not success:
            return
        source_types = ["Left", "Right", "Both"]
        success, source = self.check_value(index=1, check_list=source_types, description="extracted boob")
        if not success:
            return
        success, date = self.check_value(index=2, check_date=True, default=datetime.today().strftime('%Y-%m-%d'))
        if not success:
            return
        success, time = self.check_value(index=3, check_time=True, default=datetime.now().strftime('%H:%M:%S'))
        if not success:
            return

        day_total = 0.0
        query = f'SELECT amount FROM pump WHERE date = "{date}" AND  user_id = "{str(self._job.chat_id)}"'
        result = list(self._db.run_sql(query, fetch_all=1))
        for val in result:
            day_total = day_total + val[0]
        day_total = day_total + float(amount)

        columns = "date, time, amount, breast, user_id"
        val = (date, time, float(amount), source, str(self._job.chat_id))
        self._db.insert('pump', columns, val)

        self.send_message(message=f'\U0001F37C\nYou pumped {amount}ml on {date} at {time} from {source} boob.'
                                  f'for a total of {day_total} today!')
        self._job.complete()

    def diaper(self):
        source_types = ["Pee", "Poo", "PooPee"]
        success, source = self.check_value(index=0, check_list=source_types, description="type")
        if not success:
            return
        success, date = self.check_value(index=1, check_date=True, default=datetime.today().strftime('%Y-%m-%d'))
        if not success:
            return
        success, time = self.check_value(index=2, check_time=True, default=datetime.now().strftime('%H:%M:%S'))
        if not success:
            return

        columns = "date, time, what, count, added_by"

        if source == "Pee":
            emoji = '\U0001F6BC \U0001F4A6'
            self._db.insert('diaper', columns, (date, time, "pee", 1, str(self._job.chat_id)))
        elif source == "Poo":
            emoji = '\U0001F6BC \U0001F4A9'
            self._db.insert('diaper', columns, (date, time, "poo", 1, str(self._job.chat_id)))
        elif source == "PooPee":
            emoji = '\U0001F6BC \U0001F4A6 \U0001F4A9'
            self._db.insert('diaper', columns, (date, time, "pee", 1, str(self._job.chat_id)))
            self._db.insert('diaper', columns, (date, time, "poo", 1, str(self._job.chat_id)))
        else:
            raise ImpossibleException(f"{source} did not match Pee, Poo or PooPee")

        day_total = 0
        query = f'SELECT count FROM diaper WHERE date = "{date}"'
        result = list(self._db.run_sql(query, fetch_all=1))
        for val in result:
            day_total = day_total + val[0]

        self.send_message(message=f"{emoji}\n{source} diaper recorded on {date} at {time}.\nYour baby has had "
                                  f"{str(day_total)} nappy/diaper changes today.\nUse /diaper to submit a new entry")
        self._job.complete()

    def weight(self):
        success, weight = self.check_value(index=0, replace_str="kg", check_float=True, description="weight")
        if not success:
            return
        success, date = self.check_value(index=1, check_date=True, default=datetime.today().strftime('%Y-%m-%d'))
        if not success:
            return

        query = 'SELECT date, weight FROM weight ORDER BY weight_id DESC LIMIT 1;'
        last_entry = self._db.run_sql(query=query)

        columns = "date, weight, added_by"
        val = (date, weight, str(self._job.chat_id))
        self._db.insert('weight', columns, val)

        send_string = "\U0001F6BC \U0001F3C6 \nbaby Weight Added - " + weight + "kg. \nThat's a weight gain of " + \
                      "{:10.2f}".format(weight - last_entry[1]) + "kg since " + str(last_entry[0]) + "."

        logger.log(self._job.job_id, send_string)
        self.baby_weight_trend(caption=send_string)
        self._job.complete()

    def baby_weight_trend(self, caption=None):
        query = 'SELECT date, weight FROM weight ORDER BY timestamp'
        result = list(self._db.run_sql(query, fetch_all=1))

        if caption is None:
            caption = "\U0001F37C \U0001F3C6 \nBaby Weight trend. Add new weight using /weight command"

        pic = grapher_simple_trend(graph_list=result,
                                   x_name="Date",
                                   y_name="Weight (kg)",
                                   chart_title="Baby Weight Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        self.send_message(message=caption, group=self._group, image=pic)

        pic = grapher_weight_trend(graph_list=result,
                                   chart_title="Baby Weight Trend WHO - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        self.send_message(message="WHO Chart", group=self._group, image=pic)
        self._job.complete()

    def baby_feed_history(self):
        query = 'SELECT date, source, amount FROM feed ORDER BY timestamp'
        result = list(self._db.run_sql(query, fetch_all=1))

        pic = grapher_category(graph_list=result,
                               x_name="Date",
                               y_name="Amount (ml)",
                               chart_title="Feed History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        today = datetime.now().strftime('%Y-%m-%d')
        query = f'SELECT source, amount FROM feed WHERE date = "{today}"'
        result = list(self._db.run_sql(query, fetch_all=1))

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
            caption = caption + "\nUse /feed to submit a new entry."

        self.send_message(message=caption, group=self._group, image=pic)
        self._job.complete()

    def baby_diaper_history(self):
        query = 'SELECT date, what, count FROM diaper ORDER BY timestamp'
        result = list(self._db.run_sql(query, fetch_all=1))

        pic = grapher_category(graph_list=result,
                               x_name="Date",
                               y_name="Diapers",
                               chart_title="Diaper History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        today = datetime.now().strftime('%Y-%m-%d')
        query = f'SELECT what, count FROM diaper WHERE date = "{today}"'
        result = list(self._db.run_sql(query, fetch_all=1))

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
            caption = caption + "\nUse /diaper to submit a new entry."

        self.send_message(message=caption, group=self._group, image=pic)
        self._job.complete()

    def baby_feed_trend(self):
        query = 'SELECT time, amount, date FROM feed ORDER BY timestamp'
        result = list(self._db.run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (ml)",
                                chart_title="Feed Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)

        caption = "Use /feed to submit a new entry."
        self.send_message(message=caption, group=self._group, image=pic)

    def baby_diaper_trend(self):
        query = 'SELECT time, count, date, what FROM diaper ORDER BY timestamp'
        result = list(self._db.run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (nappies/diapers)",
                                chart_title="Diaper Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)
        caption = "Use /diaper to submit a new entry."
        self.send_message(message=caption, group=self._group, image=pic)
        self._job.complete()

    def baby_feed_trend_today(self):
        query = f'SELECT time, amount, date FROM feed WHERE date = "{datetime.now().strftime("%Y-%m-%d")}" ' \
                f'ORDER BY timestamp'
        result = list(self._db.run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (ml)",
                                chart_title="Feed Trend Today - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)

        query = f'SELECT time, amount, source FROM feed WHERE date = "{datetime.now().strftime("%Y-%m-%d")}" ' \
                f'ORDER BY timestamp'
        result = list(self._db.run_sql(query, fetch_all=1))

        caption = "Record:"
        for row in result:
            caption = caption + f"\n{row[0]} - {row[1]} - {row[2]}"
        caption = caption + "\nUse /feed to submit a new entry."

        self.send_message(message=caption, group=self._group, image=pic)
        self._job.complete()

    def baby_diaper_trend_today(self):
        query = f'SELECT time, count, date, what FROM diaper WHERE date = "{datetime.now().strftime("%Y-%m-%d")}" ' \
                f'ORDER BY timestamp'
        result = list(self._db.run_sql(query, fetch_all=1))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (nappies/diapers)",
                                chart_title="Diaper Trend Today - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)
        caption = "Record:"
        for row in result:
            caption = caption + f"\n{row[0]} - {row[1]} - {row[3]}"
        caption = caption + "\nUse /diaper to submit a new entry."

        self.send_message(message=caption, group=self._group, image=pic)
        self._job.complete()
