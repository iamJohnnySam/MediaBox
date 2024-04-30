import time

import schedule

import global_variables
from brains import task_queue
from brains.job import Job
from modules.reminder import Reminder
from tools import params
from tools.logger import log

master_reminder = Reminder(Job(function="reminder"))


def run_schedule_manager():

    if params.is_module_available('media'):
        schedule.every().day.at("00:30").do(add_task, "check_shows")
        schedule.every().day.at("06:30").do(add_task, "check_shows")
        schedule.every().day.at("08:30").do(add_task, "clean_up_downloads")

    if params.is_module_available('cctv'):
        schedule.every().day.at("01:00").do(add_task, "check_cctv")
        schedule.every().day.at("07:00").do(add_task, "check_cctv")

    if params.is_module_available('backup'):
        schedule.every().day.at("09:00").do(add_task, "backup_database")
        schedule.every().day.at("21:00").do(add_task, "backup_database")

    if params.is_module_available('telepot'):
        # schedule.every(60).minutes.do(add_task, func=news_read.run_code)
        schedule.every().day.at("07:00").do(master_reminder.read_news)

    # schedule.run_all(delay_seconds=2)

    log(msg="Schedules Created")

    while not global_variables.stop_all:
        schedule.run_pending()
        time.sleep(60)


def add_task(func: str = "alive"):
    task_queue.add_job(Job(function=func, background_task=True))
