import os
import sys
import time
import schedule
import threading
import platform

import global_var
from maintenance import start_up
from web import web_app
import logger
from communication import communicator
from news.news_reader import NewsReader
from show.show_downloader import ShowDownloader
from cctv.cctv_checker import CCTVChecker

# https://github.com/dbader/schedule
running_threads = {}
schedule_on_hold = {}


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


def run_scheduler():
    exit_condition = True

    schedule.every().day.at("00:30").do(schedule_handler, func=my_shows.run_code)
    schedule.every().day.at("01:00").do(schedule_handler, func=cctv.run_code)
    schedule.every(60).minutes.do(schedule_handler, func=news_read.run_code)
    schedule.every().day.at("03:00").do(schedule_handler, func=cctv.clean_up)

    schedule.run_all(delay_seconds=10)

    # schedule.every(15).minutes.do(schedule_handler, func=cctv.run_code)
    schedule.every().day.at("05:00").do(schedule_handler, func=my_shows.run_code)
    schedule.every().day.at("07:00").do(schedule_handler, func=cctv.run_code)
    schedule.every().day.at("09:00").do(schedule_handler, func=global_var.backup.backup_databases)

    while exit_condition:
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

        if global_var.stop_cctv:
            logger.log("Exiting Code")
            sys.exit()

        time.sleep(1)


def run_webapp():
    if __name__ == '__main__':
        web_app.app.run(debug=False, host='0.0.0.0')


# CHECK RUNNING SYSTEM
logger.log("Currently running code on: " + platform.machine())

if platform.machine() == 'armv7l':
    logger.log("Code Running in Full Mode")
    my_shows = ShowDownloader()
    cctv = CCTVChecker()
    news_read = NewsReader()

    global_var.ready_to_run = True
    logger.log('Program Started')

    t_scheduler = threading.Thread(target=run_scheduler)
    t_scheduler.start()

    t_webapp = threading.Thread(target=run_webapp, daemon=True)
    t_webapp.start()

    # t_scheduler.join()
    while t_scheduler.is_alive():
        for thread in list(running_threads.keys()):
            if not running_threads[thread].is_alive():
                del running_threads[thread]
                logger.log("Thread Ended: " + thread)
        time.sleep(10)

else:
    logger.log("Code Running in Partial Mode")

    t_webapp = threading.Thread(target=run_webapp)
    t_webapp.start()

    t_webapp.join()

global_var.backup.run_code()

# ------ REBOOT CONDITION -----------
if not global_var.stop_all:
    communicator.send_to_master("main", "Crashed.")
    time.sleep(60)

    logger.log("argv was" + str(sys.argv))
    logger.log("sys.executable was" + str(sys.executable))

    logger.log("Restarting now...")
    start_up.keep_gap()
    start_up.print_logo()

    python = sys.executable
    os.execv(sys.executable, ['python'] + sys.argv)

else:
    communicator.send_to_master("main", "Exiting...")
    logger.log("EXIT")

    if global_var.reboot_pi:
        os.system("sudo reboot")
