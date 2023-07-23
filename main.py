import time
import schedule
import threading

import WebApp
import logger
from ShowDownloader import ShowDownloader
from CCTVChecker import CCTVChecker

# https://github.com/dbader/schedule

my_shows = ShowDownloader()
cctv = CCTVChecker()

logger.log('info', 'Program Started')


def run_scheduler():
    exit_condition = True

    schedule.every().day.at("00:30").do(my_shows.run_code)
    schedule.every().day.at("01:30").do(cctv.run_code)
    schedule.every().day.at("05:00").do(my_shows.run_code)

    my_shows.run_code()
    cctv.run_code()
    cctv.clear_sent()

    while exit_condition:
        schedule.run_pending()
        time.sleep(1)


t_scheduler = threading.Thread(target=run_scheduler)
t_scheduler.start()

if __name__ == '__main__':
    WebApp.app.run(debug=True, host='0.0.0.0')
