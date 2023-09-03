import time
import schedule
import threading

import global_var
import web_app
import logger
import communicator

from show_downloader import ShowDownloader
from cctv_checker import CCTVChecker

# https://github.com/dbader/schedule

my_shows = ShowDownloader()
cctv = CCTVChecker()

logger.log('info', 'Program Started')


def run_scheduler():
    exit_condition = True

    schedule.every().day.at("00:30").do(my_shows.run_code)
    schedule.every(15).minutes.do(cctv.run_code)
    schedule.every().day.at("05:00").do(my_shows.run_code)

    my_shows.run_code()
    cctv.run_code()

    while exit_condition:
        schedule.run_pending()
        if global_var.check_shows:
            my_shows.run_code()
            global_var.check_shows = False
        time.sleep(1)


communicator.start()

t_scheduler = threading.Thread(target=run_scheduler)
t_scheduler.start()

if __name__ == '__main__':
    web_app.app.run(debug=False, host='0.0.0.0')
