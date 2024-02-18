from datetime import datetime

import global_var
import logger
from cctv.cctv_checker import CCTVChecker
from communication.channels import channels
from module.job import Job
from database_manager.sql_connector import sql_databases
from news.news_reader import NewsReader
from show.movie_finder import MovieFinder
from show.show_downloader import ShowDownloader


class Task:
    def __init__(self, telepot_channel="main"):
        self.channel = channels[telepot_channel]
        logger.log(f"Task Created for channel {self.channel}.")




    def handle_message(self, msg: Job):
        # todo if not called back then start() else resume()
        if msg.called_back:
           pass
        else:
            pass





    def no_function(self, msg: Job):
        button_text = ["save_photo"]
        for key in self.command_dictionary.keys():
            if type(self.command_dictionary[key]) is dict and "photo" in self.command_dictionary[key].keys():
                button_text.append(f'{self.command_dictionary[key]["function"]}_photo')

        button_text, button_cb, button_value, arrangement = self.keyboard_extractor(msg.photo_name, None,
                                                                                    button_text,
                                                                                    'run_command',
                                                                                    sql_result=False,
                                                                                    command_only=True)
        self.send_with_keyboard(msg="Which function to call?",
                                chat_id=msg.chat_id,
                                button_text=button_text,
                                button_cb=button_cb,
                                button_val=button_value,
                                arrangement=arrangement,
                                reply_to=msg.message_id
                                )

    def check_shows(self, msg: Job):
        ShowDownloader(msg).run_code()
        msg.complete()

    def check_news(self, msg: Job):
        NewsReader(msg).run_code()
        msg.complete()

    def check_cctv(self, msg: Job):
        CCTVChecker(msg).run_code()
        msg.complete()

    def find_movie(self, msg: Job):
        MovieFinder(msg).find_movie()

    def request_tv_show(self, msg: Job):
        if not self.check_command_value(msg, inquiry="name of TV show"):
            return

        sql_databases["entertainment"].insert("requested_shows",
                                              "name, requested_by, requested_id",
                                              (msg.value, msg.f_name, msg.chat_id))
        logger.log("TV Show Requested - " + msg.value)
        self.send_now("TV Show Requested - " + msg.value, chat=msg.chat_id, reply_to=msg.message_id)
        self.send_now("TV Show Requested - " + msg.value)







