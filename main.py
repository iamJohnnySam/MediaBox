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


def run_threader(func):
    function = func.__qualname__
    if function in running_threads.keys():
        logger.log("Busy. Cannot Start thread for " + function)
        return False

    running_threads[function] = threading.Thread(target=func)
    running_threads[function].start()

    logger.log("Started Thread " + function)
    return True


def scheduler(name):
    if name == "show":
        success = run_threader(my_shows.run_code)
    elif name == "cctv":
        success = run_threader(cctv.run_code)
    elif name == "cctv_clean":
        success = run_threader(cctv.clean_up)
    elif name == "news":
        success = run_threader(news_read.run_code)
    else:
        logger.log("Schedule Call Error", message_type="err")
        return

    if success and name in schedule_on_hold.keys():
        schedule.cancel_job(schedule_on_hold[name])
        del schedule_on_hold[name]
    elif name not in schedule_on_hold.keys():
        schedule_on_hold[name] = schedule.every(15).minutes.do(scheduler, name=name)
    else:
        return


def run_scheduler():
    exit_condition = True

    schedule.every().day.at("00:30").do(scheduler, name='show')
    schedule.every().day.at("01:00").do(scheduler, name='cctv')
    # schedule.every(15).minutes.do(scheduler, name='cctv')
    schedule.every(60).minutes.do(scheduler, name='news')
    schedule.every().day.at("05:00").do(scheduler, name='show')
    schedule.every().day.at("03:00").do(scheduler, name='cctv_clean')

    schedule.run_all(delay_seconds=10)

    while exit_condition:
        schedule.run_pending()
        if global_var.check_shows:
            global_var.check_shows = False
            scheduler("show")

        if global_var.check_cctv:
            global_var.check_cctv = False
            scheduler("cctv")

        if global_var.check_news:
            global_var.check_news = False
            scheduler("news")

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
        for thread in running_threads.keys():
            if not running_threads[thread].is_alive():
                del running_threads[thread]

else:
    logger.log("Code Running in Partial Mode")

    t_webapp = threading.Thread(target=run_webapp)
    t_webapp.start()

    t_webapp.join()

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
