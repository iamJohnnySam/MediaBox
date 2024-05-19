import time

import schedule

from common_workspace import global_var
from job_handler import task_queue
from shared_models import configuration
from shared_models.job import Job
from job_handler.modules.reminder import Reminder
from shared_tools.configuration_tools import is_config_enabled
from shared_tools.logger import log


def run_scheduler():
    config = configuration.Configuration()

    if is_config_enabled(config.media):
        schedule.every().day.at("00:30").do(add_task, "check_shows")
        schedule.every().day.at("06:30").do(add_task, "check_shows")
        schedule.every().day.at("08:30").do(add_task, "clean_up_downloads")

    if is_config_enabled(config.cctv):
        schedule.every().day.at("01:00").do(add_task, "check_cctv")
        schedule.every().day.at("07:00").do(add_task, "check_cctv")

    schedule.every().day.at("09:00").do(add_task, "backup_database")
    schedule.every().day.at("21:00").do(add_task, "backup_database")

    if is_config_enabled(config.telegram):
        master_reminder = Reminder(Job(function="reminder"))
        # schedule.every(60).minutes.do(add_task, func=news_read.run_code)
        schedule.every().day.at("07:00").do(master_reminder.read_news)

    # schedule.run_all(delay_seconds=2)

    log(msg="Schedules Created")

    while not global_var.flag_stop.value:
        schedule.run_pending()
        time.sleep(60)


def add_task(func: str = "alive"):
    task_queue.add_job(Job(function=func, background_task=True))
