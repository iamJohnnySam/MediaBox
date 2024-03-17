import sys
import threading
import time

import schedule

import global_variables
from tools import logger

run_all_schedules = False
running_threads = {}
schedule_on_hold = {}


def run_schedule_manager():
    t_scheduler = threading.Thread(target=run_scheduler)
    t_scheduler.start()
    logger.log(msg="Thread Started: Scheduler")

    # todo create default schedule tasks
    '''schedule.every().day.at("00:30").do(schedule_handler, func=my_shows.run_code)
    logger.log("Schedule Created for Show Downloader")

    schedule.every().day.at("01:00").do(schedule_handler, func=ai_models.run_code)
    logger.log("Schedule Created for CCTV Checker")

    schedule.every(60).minutes.do(schedule_handler, func=news_read.run_code)
    logger.log("Schedule Created for News Reader")

    schedule.every().day.at("03:00").do(schedule_handler, func=ai_models.clean_up)
    logger.log("Schedule Created for CCTV Email Clean up")

    schedule.run_all(delay_seconds=2)

    schedule.every().day.at("05:00").do(schedule_handler, func=my_shows.run_code)
    logger.log("Schedule Created for Show Downloader")

    schedule.every().day.at("07:00").do(schedule_handler, func=ai_models.run_code)
    logger.log("Schedule Created for CCTV Checker")

    schedule.every().day.at("09:00").do(schedule_handler, func=backup.backup.cp_databases)
    logger.log("Schedule Created for Database Backup")

    schedule.every().day.at("08:30").do(schedule_handler, func=transmission.torrent_complete_sequence)
    logger.log("Schedule Created for Download Cleanup")'''

    while t_scheduler.is_alive() and not global_var.stop_all:
        check_running_threads()
        time.sleep(10)

    global_var.stop_all = True


def run_scheduler():
    global run_all_schedules

    while not global_var.stop_all:

        if run_all_schedules:
            run_all_schedules = False
            schedule.run_all(delay_seconds=2)

        schedule.run_pending()
        time.sleep(1)

    logger.log(msg="Exiting Scheduler")
    sys.exit()


def schedule_handler(func):
    name = func.__qualname__
    function = name.split(".")[0]
    if function in running_threads.keys():
        logger.log("BUSY. Cannot Start thread for " + function, log_type="warn")
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
