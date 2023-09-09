import os
import sys
import time
import schedule
import threading

import global_var
import web_app
import logger
import communicator
from news_reader import NewsReader

from show_downloader import ShowDownloader
from cctv_checker import CCTVChecker

# https://github.com/dbader/schedule

my_shows = ShowDownloader()
cctv = CCTVChecker()
news_read = NewsReader()

logger.log('info', 'Program Started')


def run_scheduler():
    exit_condition = True

    schedule.every().day.at("00:30").do(my_shows.run_code)
    schedule.every(15).minutes.do(cctv.run_code)
    schedule.every(60).minutes.do(news_read.run_code)
    schedule.every().day.at("05:00").do(my_shows.run_code)

    my_shows.run_code()
    cctv.run_code()
    news_read.run_code()

    while exit_condition:
        schedule.run_pending()
        if global_var.check_shows:
            my_shows.run_code()
            global_var.check_shows = False
        if global_var.check_cctv:
            cctv.run_code()
            global_var.check_cctv = False

        if global_var.connection_err >= 4:
            sys.exit()

        time.sleep(1)


def run_webapp():
    if __name__ == '__main__':
        web_app.app.run(debug=False, host='0.0.0.0')


communicator.start()

t_scheduler = threading.Thread(target=run_scheduler)
t_scheduler.start()

t_webapp = threading.Thread(target=run_webapp, daemon=True)
t_webapp.start()

# Wait for all threads to close
t_scheduler.join()

print("argv was", sys.argv)
print("sys.executable was", sys.executable)

time.sleep(60)

print("restarting now")
print("-----------------------")
print("")
print("")
print("")

python = sys.executable
os.execv(sys.executable, ['python'] + sys.argv)
