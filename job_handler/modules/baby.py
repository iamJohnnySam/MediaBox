from datetime import datetime, timedelta

import refs
from shared_models.message import Message
from database_manager.sql_connector import SQLConnector
from shared_tools.grapher import grapher_simple_trend, grapher_weight_trend, grapher_category, grapher_bar_trend
from shared_tools.custom_exceptions import *
from shared_models.job import Job
from job_handler.base_module import Module
from shared_tools.logger import log


class Baby(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        self._db = SQLConnector(job.job_id, database=refs.db_baby)
        log(self._job.job_id, f"Baby Module Created")
        self._group = "baby"

    def feed(self):
        amount_list = ["30ml", "60ml", "90ml", "120ml"]
        success, amount = self.check_value(index=0, replace_str="ml", check_float=True, option_list=amount_list,
                                           description="amount consumed")
        if not success:
            return
        source_types = ["breast", "express", "formula"]
        success, source = self.check_value(index=1, check_list=source_types, default="formula",
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

        columns = "date, time, amount, source, added_by"
        val = (date, time, float(amount), source, str(self._job.chat_id))
        self._db.insert(refs.tbl_baby_feed, columns, val)

        day_total = self._get_total(refs.tbl_baby_feed, "amount", date)
        average: int = self._get_seven_day_average(refs.tbl_baby_feed, "amount", date)

        self.send_message(Message(f'\U0001F37C\nBaby was fed {amount}ml on {date} at {time} with {source} milk '
                                  f'for a total of {"{:10.1f}".format(day_total).strip()}ml today - {average}%.'
                                  f'\nUse /feed to submit a new entry',
                                  job=self._job,
                                  group=self._group), channel="baby")
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

        columns = "date, time, amount, breast, user_id"
        val = (date, time, float(amount), source, str(self._job.chat_id))
        self._db.insert(refs.tbl_baby_pump, columns, val)

        day_total = self._get_total(refs.tbl_baby_pump, "amount", date, user_id=True)

        self.send_message(Message(f'\U0001F37C\nYou pumped {amount}ml on {date} at {time} from {source} boob.'
                                  f'for a total of {day_total} today!', job=self._job))
        self._job.complete()

    def diaper(self):
        source_types = ["pee", "poo", "poopee"]
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

        if source == "pee":
            emoji = '\U0001F6BC \U0001F4A6'
            self._db.insert(refs.tbl_baby_diaper, columns, (date, time, "pee", 1, str(self._job.chat_id)))
        elif source == "poo":
            emoji = '\U0001F6BC \U0001F4A9'
            self._db.insert(refs.tbl_baby_diaper, columns, (date, time, "poo", 1, str(self._job.chat_id)))
        elif source == "poopee":
            emoji = '\U0001F6BC \U0001F4A6 \U0001F4A9'
            self._db.insert(refs.tbl_baby_diaper, columns, (date, time, "pee", 1, str(self._job.chat_id)))
            self._db.insert(refs.tbl_baby_diaper, columns, (date, time, "poo", 1, str(self._job.chat_id)))
        else:
            raise ImpossibleException(f"{source} did not match Pee, Poo or PooPee")

        day_total = 0
        result = list(self._db.select(table=refs.tbl_baby_diaper,
                                      columns="count", where={"date": date}, fetch_all=True))
        for val in result:
            day_total = day_total + val[0]

        self.send_message(Message(f"{emoji}\n{source} diaper recorded on {date} at {time}.\nYour baby has had "
                                  f"{str(day_total)} nappy/diaper changes today.\nUse /diaper to submit a new entry",
                                  job=self._job,
                                  group=self._group), channel="baby")
        self._job.complete()

    def weight(self):
        success, weight = self.check_value(index=0, replace_str="kg", check_float=True, description="weight")
        if not success:
            return
        success, date = self.check_value(index=1, check_date=True, default=datetime.today().strftime('%Y-%m-%d'))
        if not success:
            return

        last_entry = self._db.select(table=refs.tbl_baby_weight,
                                     columns="date, weight",
                                     order="weight_id", ascending=False, limit=1)

        columns = "date, weight, added_by"
        val = (date, weight, str(self._job.chat_id))
        self._db.insert(refs.tbl_baby_weight, columns, val)

        send_string = f"\U0001F6BC \U0001F3C6 \nbaby Weight Added - {weight}kg. \n" \
                      f"That's a weight gain of {(float(weight) - last_entry[1]):10.2f}kg since {last_entry[0]}."

        log(self._job.job_id, send_string)
        self.weight_trend(caption=send_string)
        self._job.complete()

    def weight_trend(self, caption=None):
        result = list(self._db.select(table=refs.tbl_baby_weight,
                                      columns="date, weight", order="timestamp", fetch_all=True))

        if caption is None:
            caption = "\U0001F37C \U0001F3C6 \nBaby Weight trend. Add new weight using /weight command"

        pic = grapher_simple_trend(graph_list=result,
                                   x_name="Date",
                                   y_name="Weight (kg)",
                                   chart_title="Baby Weight Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        self.send_message(Message(caption, group=self._group, photo=pic), channel="baby")

        pic = grapher_weight_trend(graph_list=result,
                                   chart_title="Baby Weight Trend WHO - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        self.send_message(Message("WHO Chart", group=self._group, photo=pic))
        self._job.complete()

    def feed_history(self):
        result = list(self._db.select(table=refs.tbl_baby_feed,
                                      columns="date, source, amount", order="timestamp", fetch_all=True))

        pic = grapher_category(graph_list=result,
                               x_name="Date",
                               y_name="Amount (ml)",
                               chart_title="Feed History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        result = list(self._db.select(table=refs.tbl_baby_feed,
                                      columns="source, amount",
                                      where={"date": datetime.now().strftime('%Y-%m-%d')},
                                      order="timestamp", fetch_all=True))
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

        self.send_message(Message(caption, job=self._job, photo=pic))
        self._job.complete()

    def diaper_history(self):
        result = list(self._db.select(table=refs.tbl_baby_diaper,
                                      columns="date, what, count", order="timestamp", fetch_all=True))

        pic = grapher_category(graph_list=result,
                               x_name="Date",
                               y_name="Diapers",
                               chart_title="Diaper History - " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        result = list(self._db.select(table=refs.tbl_baby_diaper,
                                      columns="what, count",
                                      where={"date": datetime.now().strftime('%Y-%m-%d')},
                                      order="timestamp", fetch_all=True))

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

        self.send_message(Message(caption, job=self._job, photo=pic))
        self._job.complete()

    def feed_trend(self):
        result = list(self._db.select(table=refs.tbl_baby_feed,
                                      columns="time, amount, date", order="timestamp", fetch_all=True))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (ml)",
                                chart_title="Feed Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)

        caption = "Use /feed to submit a new entry."
        self.send_message(Message(caption, job=self._job, photo=pic))

    def diaper_trend(self):
        result = list(self._db.select(table=refs.tbl_baby_diaper,
                                      columns="time, count, date, what", order="timestamp", fetch_all=True))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (nappies/diapers)",
                                chart_title="Diaper Trend - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)
        caption = "Use /diaper to submit a new entry."
        self.send_message(Message(caption, job=self._job, photo=pic))
        self._job.complete()

    def feed_trend_today(self):
        result = list(self._db.select(table=refs.tbl_baby_feed,
                                      columns="time, amount, date",
                                      where={"date": datetime.now().strftime("%Y-%m-%d")},
                                      order="timestamp", fetch_all=True))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (ml)",
                                chart_title="Feed Trend Today - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)

        result = list(self._db.select(table=refs.tbl_baby_feed,
                                      columns="time, amount, source",
                                      where={"date": datetime.now().strftime("%Y-%m-%d")},
                                      order="timestamp", fetch_all=True))

        caption = "Record:"
        for row in result:
            caption = caption + f"\n{row[0]} - {row[1]} - {row[2]}"
        caption = caption + "\nUse /feed to submit a new entry."

        self.send_message(Message(caption, job=self._job, photo=pic))
        self._job.complete()

    def diaper_trend_today(self):
        result = list(self._db.select(table=refs.tbl_baby_diaper,
                                      columns="time, count, date, what",
                                      where={"date": datetime.now().strftime("%Y-%m-%d")},
                                      order="timestamp", fetch_all=True))

        pic = grapher_bar_trend(graph_list=result,
                                x_name="Time of Day (round to nearest hour)",
                                y_name="Amount (nappies/diapers)",
                                chart_title="Diaper Trend Today - " + datetime.now().strftime('%Y-%m-%d %H:%M'),
                                x_time=True)
        caption = "Record:"
        for row in result:
            caption = caption + f"\n{row[0]} - {row[1]} - {row[3]}"
        caption = caption + "\nUse /diaper to submit a new entry."

        self.send_message(Message(caption, job=self._job, photo=pic))
        self._job.complete()

    def _get_total(self, table, col, date, user_id: bool = False):
        where = {"date": date}
        if user_id:
            where["user_id"] = self._job.chat_id

        total = 0.0
        result = list(self._db.select(table=table, columns=col, where=where, fetch_all=True))

        for val in result:
            total = total + val[0]
        return total

    def _get_seven_day_average(self, table, col, date, user_id: bool = False, today_tot=0):
        if today_tot == 0:
            today_tot = self._get_total(table, col, date, user_id)

        avg = [0, 0, 0, 0, 0, 0, 0]
        for i in range(len(avg)):
            new_date = datetime.strptime(date, '%Y-%m-%d') - timedelta(days=i + 1)
            avg[i] = self._get_total(table, col, new_date.strftime('%Y-%m-%d'), user_id)

        try:
            average = int(today_tot * len(avg) * 100 / sum(avg))
        except ZeroDivisionError:
            average = 0

        return average
