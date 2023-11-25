import os
import sys
import time
import schedule
import threading
import platform

import global_var
from web import web_app
import logger
from communication import communicator
from news.news_reader import NewsReader
from show.show_downloader import ShowDownloader
from cctv.cctv_checker import CCTVChecker

# https://github.com/dbader/schedule

# CHECK RUNNING SYSTEM
print("Currently running code on: ", platform.machine())
if platform.machine() == 'armv7l':
    run_all = True
else:
    run_all = False
    print("Running on other platform (not Raspberry Pi)")

# CREATE OBJECTS
if run_all:
    my_shows = ShowDownloader()
    cctv = CCTVChecker()
    news_read = NewsReader()

logger.log('info', 'Program Started')


def run_scheduler():
    exit_condition = True

    schedule.every().day.at("00:30").do(my_shows.run_code)
    schedule.every().day.at("00:30").do(cctv.run_code)
    # schedule.every(15).minutes.do(cctv.run_code)
    schedule.every(60).minutes.do(news_read.run_code)
    schedule.every().day.at("05:00").do(my_shows.run_code)

    my_shows.run_code()
    cctv.run_code()
    news_read.run_code()

    while exit_condition:
        schedule.run_pending()
        if global_var.check_shows:
            global_var.check_shows = False
            my_shows.run_code()
        if global_var.check_cctv:
            global_var.check_cctv = False
            cctv.run_code()
        if global_var.check_news:
            news_read.run_code()
            global_var.check_news = False

        if global_var.stop_cctv:
            communicator.send_to_master("main", "Exiting...")
            sys.exit()

        time.sleep(1)


def run_webapp():
    if __name__ == '__main__':
        web_app.app.run(debug=False, host='0.0.0.0')


if run_all:
    t_scheduler = threading.Thread(target=run_scheduler)
    t_scheduler.start()

    t_webapp = threading.Thread(target=run_webapp, daemon=True)
    t_webapp.start()

    t_scheduler.join()

else:
    t_webapp = threading.Thread(target=run_webapp)
    t_webapp.start()

    t_webapp.join()


print("argv was", sys.argv)
print("sys.executable was", sys.executable)

if not global_var.stop_all:
    time.sleep(60)

    communicator.send_to_master("main", "Restarting...")
    print("restarting now")
    print("-----------------------")
    print("")
    print("")
    print("")

    python = sys.executable
    os.execv(sys.executable, ['python'] + sys.argv)
