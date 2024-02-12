from datetime import datetime

import global_var
import logger
from cctv.cctv_checker import CCTVChecker
from communication.channels import channels
from communication.message import Message
from database_manager.sql_connector import sql_databases
from news.news_reader import NewsReader
from show.movie_finder import MovieFinder
from show.show_downloader import ShowDownloader


class Task:
    def __init__(self, telepot_channel="main"):
        self.channel = channels[telepot_channel]
        logger.log(f"Task Created for channel {self.channel}.")




    def handle_message(self, msg: Message):
        # todo if not called back then start() else resume()
        if msg.called_back:
           pass
        else:
            pass



    def alive(self, msg: Message):
        self.channel.send_now(f"{str(msg.chat_id)}\nHello{msg.f_name}! I'm Alive and kicking!", msg=msg)
        msg.complete()

    def time(self, msg: Message):
        self.channel.send_now(str(datetime.now()), msg=msg)
        msg.complete()

    def start_over(self, msg: Message):
        if msg.is_master:
            global_var.stop_all = True
            global_var.stop_cctv = True
            global_var.restart = True
            self.channel.send_now("Completing ongoing tasks before restart. Please wait.", msg=msg)
        else:
            self.channel.send_now("This is a server command. Requesting admin...", msg=msg)
            self.channel.send_now(f"/start_over requested by {msg.f_name}.")
        msg.complete()

    def exit_all(self, msg: Message):
        if msg.is_master:
            global_var.stop_all = True
            global_var.stop_cctv = True
            self.channel.send_now("Completing ongoing tasks before exit. Please wait.", msg=msg)
        else:
            self.channel.send_now("This is a server command. Requesting admin...", msg=msg)
            self.channel.send_now(f"/exit_all requested by {msg.f_name}.")
        msg.complete()

    def reboot_pi(self, msg: Message):
        if msg.is_master:
            global_var.stop_all = True
            global_var.stop_cctv = True
            global_var.reboot_pi = True
            self.channel.send_now("Completing ongoing tasks before reboot. Please wait.", msg=msg)
        else:
            self.channel.send_now("This is a server command. Requesting admin...", msg=msg)
            self.channel.send_now(f"/reboot_pi requested by {msg.f_name}.")
        msg.complete()

    def no_function(self, msg: Message):
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

    def check_shows(self, msg: Message):
        ShowDownloader(msg).run_code()
        msg.complete()

    def check_news(self, msg: Message):
        NewsReader(msg).run_code()
        msg.complete()

    def check_cctv(self, msg: Message):
        CCTVChecker(msg).run_code()
        msg.complete()

    def find_movie(self, msg: Message):
        MovieFinder(msg).find_movie()

    def request_tv_show(self, msg: Message):
        if not self.check_command_value(msg, inquiry="name of TV show"):
            return

        sql_databases["entertainment"].insert("requested_shows",
                                              "name, requested_by, requested_id",
                                              (msg.value, msg.f_name, msg.chat_id))
        logger.log("TV Show Requested - " + msg.value)
        self.send_now("TV Show Requested - " + msg.value, chat=msg.chat_id, reply_to=msg.message_id)
        self.send_now("TV Show Requested - " + msg.value)







