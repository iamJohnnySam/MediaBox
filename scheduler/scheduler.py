import sys
import threading
import time

import schedule

import global_var
import logger
from cctv.cctv_checker import CCTVChecker
from maintenance import backup
from news.news_reader import NewsReader
from show.show_downloader import ShowDownloader

running_threads = {}
schedule_on_hold = {}

my_shows = ShowDownloader()
cctv = CCTVChecker()
news_read = NewsReader()


def schedule_handler(func):
    name = func.__qualname__
    function = name.split(".")[0]
    if function in running_threads.keys():
        logger.log("BUSY. Cannot Start thread for " + function, message_type="warn")
        if name not in schedule_on_hold.keys():
            schedule_on_hold[name] = schedule.every(1).minutes.do(schedule_handler, func=func)

        return

    running_threads[function] = threading.Thread(target=func)
    running_threads[function].start()

    logger.log("Thread Started: " + function)
    if name in list(schedule_on_hold.keys()):
        schedule.cancel_job(schedule_on_hold[name])
        del schedule_on_hold[name]


def check_running_threads():
    for thread in list(running_threads.keys()):
        if not running_threads[thread].is_alive():
            del running_threads[thread]
            logger.log("Thread Ended: " + thread)


def run_scheduler():
    schedule.every().day.at("00:30").do(schedule_handler, func=my_shows.run_code)
    logger.log("Schedule Created for Show Downloader")

    schedule.every().day.at("01:00").do(schedule_handler, func=cctv.run_code)
    logger.log("Schedule Created for CCTV Checker")

    schedule.every(60).minutes.do(schedule_handler, func=news_read.run_code)
    logger.log("Schedule Created for News Reader")

    schedule.every().day.at("03:00").do(schedule_handler, func=cctv.clean_up)
    logger.log("Schedule Created for CCTV Email Clean up")

    schedule.run_all(delay_seconds=2)

    schedule.every().day.at("05:00").do(schedule_handler, func=my_shows.run_code)
    logger.log("Schedule Created for Show Downloader")

    schedule.every().day.at("07:00").do(schedule_handler, func=cctv.run_code)
    logger.log("Schedule Created for CCTV Checker")

    schedule.every().day.at("09:00").do(schedule_handler, func=backup.backup.cp_databases)
    logger.log("Schedule Created for Database Backup")

    while not global_var.stop_all:
        schedule.run_pending()

        if global_var.check_shows:
            global_var.check_shows = False
            schedule_handler(my_shows.run_code)

        if global_var.check_cctv:
            global_var.check_cctv = False
            schedule_handler(cctv.run_code)

        if global_var.check_news:
            global_var.check_news = False
            schedule_handler(news_read.run_code)

        time.sleep(1)

    logger.log("Exiting Scheduler")
    sys.exit()
