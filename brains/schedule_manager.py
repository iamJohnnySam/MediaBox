import time

import schedule

import global_variables
from brains import task_queue
from brains.job import Job
from tools.logger import log


def run_schedule_manager():
    schedule.every().day.at("00:30").do(add_task, Job(function="check_shows"))
    schedule.every().day.at("01:00").do(add_task, Job(function="check_cctv"))
    # schedule.every(60).minutes.do(add_task, func=news_read.run_code)
    schedule.every().day.at("09:00").do(add_task, Job(function="backup_database"))
    schedule.run_all(delay_seconds=2)
    schedule.every().day.at("05:00").do(add_task, Job(function="check_shows"))
    schedule.every().day.at("07:00").do(add_task, Job(function="check_cctv"))
    schedule.every().day.at("08:30").do(add_task, Job(function="clean_up_downloads"))
    schedule.every().day.at("21:00").do(add_task, Job(function="backup_database"))

    log(msg="Schedules Created")

    while not global_variables.stop_all:
        schedule.run_pending()
        time.sleep(1)


def add_task(job: Job):
    task_queue.add_job(job)
