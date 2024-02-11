from datetime import datetime

import global_var
import logger
from cctv.cctv_checker import CCTVChecker
from communication.channels import channels
from communication.message import Message
from news.news_reader import NewsReader
from show.show_downloader import ShowDownloader


class Task:
    def __init__(self, telepot_channel="main"):
        logger.log(f"Task Created for channel {telepot_channel}.")

        self.channel = channels[telepot_channel]

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

    def check_shows(self, msg: Message):
        ShowDownloader(msg).run_code()
        msg.complete()

    def check_news(self, msg: Message):
        NewsReader(msg).run_code()
        msg.complete()

    def check_cctv(self, msg: Message):
        CCTVChecker(msg).run_code()
        msg.complete()

    def request_tv_show(self, msg: Message):
        if not self.check_command_value(msg, inquiry="name of TV show"):
            return

        sql_databases["entertainment"].insert("requested_shows",
                                              "name, requested_by, requested_id",
                                              (msg.value, msg.f_name, msg.chat_id))
        logger.log("TV Show Requested - " + msg.value)
        self.send_now("TV Show Requested - " + msg.value, chat=msg.chat_id, reply_to=msg.message_id)
        self.send_now("TV Show Requested - " + msg.value)



