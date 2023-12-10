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

print("")
print("")
print("")


def run_scheduler():
    exit_condition = True

    schedule.every().day.at("00:30").do(my_shows.run_code)
    schedule.every().day.at("01:00").do(cctv.run_code)
    # schedule.every(15).minutes.do(cctv.run_code)
    schedule.every(60).minutes.do(news_read.run_code)
    schedule.every().day.at("05:00").do(my_shows.run_code)
    schedule.every().day.at("03:00").do(cctv.clean_up)

    my_shows.run_code()
    cctv.run_code()
    news_read.run_code()
    cctv.clean_up()

    while exit_condition:
        schedule.run_pending()
        if global_var.check_shows:
            global_var.check_shows = False
            my_shows.run_code()

        if global_var.check_cctv:
            global_var.check_cctv = False
            cctv.run_code()

        if global_var.check_news:
            global_var.check_news = False
            news_read.run_code()

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

    t_scheduler.join()

else:
    logger.log("Code Running in Partial Mode")

    t_webapp = threading.Thread(target=run_webapp)
    t_webapp.start()

    t_webapp.join()

if not global_var.stop_all:
    time.sleep(60)

    logger.log("argv was" + sys.argv)
    logger.log("sys.executable was" + sys.executable)

    logger.log("Restarting now...")
    print("")
    print("")
    print("")

    python = sys.executable
    os.execv(sys.executable, ['python'] + sys.argv)

else:
    communicator.send_to_master("main", "Exiting...")
    logger.log("EXIT")

    if global_var.reboot_pi:
        os.system("sudo reboot")
