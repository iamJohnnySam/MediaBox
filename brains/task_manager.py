import threading
import time

import global_variables
from brains import task_queue
from brains.job import Job
from modules.admin import Admin
from modules.baby import Baby
from modules.backup import BackUp
from modules.movie_finder import MovieFinder
from modules.transmission import Transmission
from tools.logger import log

running_tasks = {}


def run_task_manager():
    while not global_variables.ready_to_run:
        time.sleep(5)

    log(msg="Task Manager Started")

    while not global_variables.stop_all:
        while not task_queue.job_q.empty():
            job: Job = task_queue.get_job()

            check_running_tasks()

            if job.job_id in running_tasks.keys():
                log(job.job_id, "Waiting for Job to complete to process next task")
                task_queue.add_job(job)
                continue

            if job.job_id != 0:
                running_tasks[job.job_id] = threading.Thread(target=run_task, args=(job,))
                running_tasks[job.job_id].start()
            else:
                threading.Thread(target=run_task, args=(job,)).start()

        time.sleep(1)


def run_task(job: Job):
    job.update_job()
    func = job.function
    if func == "alive":
        Admin(job).alive()
    elif func == "time":
        Admin(job).time()
    elif func == "help":
        Admin(job).help()
    elif func == "backup_all":
        if global_variables.operation_mode:
            backup = BackUp(job, '/mnt/MediaBox/MediaBox/Backup')
            backup.move_folders.append('log/')
            backup.move_png_files.append('charts/')
            backup.copy_files.append('passwords.py')
            backup.move_files.append('../nohup.out')
            backup.run_backup()
        else:
            log(job.job_id, "Unable to run back up. Not in Operation Mode", "warn")

    elif func == "check_shows":
        Transmission(job).list_torrents()
    elif func == "find_movie":
        MovieFinder(job).find_movie()
    elif func == "request_tv_show":
        pass

    elif func == "check_news":
        pass
    elif func == "subscribe_news":
        pass
    elif func == "add_me_to_news":
        pass
    elif func == "remove_me_from_news":
        pass

    elif func == "check_cctv":
        pass
    elif func == "add_me_to_cctv":
        pass
    elif func == "remove_me_from_cctv":
        pass

    elif func == "list_torrents":
        pass
    elif func == "clean_up_downloads":
        pass

    elif func == "finance":
        pass
    elif func == "sms_bill":
        pass

    elif func == "add_me_to_baby":
        pass
    elif func == "remove_me_from_baby":
        pass
    elif func == "baby_feed":
        Baby(job).feed()
    elif func == "baby_feed_history":
        Baby(job).feed_history()
    elif func == "baby_feed_trend":
        Baby(job).feed_trend()
    elif func == "baby_feed_trend_today":
        Baby(job).feed_trend_today()
    elif func == "baby_diaper":
        Baby(job).diaper()
    elif func == "baby_diaper_history":
        Baby(job).diaper_history()
    elif func == "baby_diaper_trend":
        Baby(job).diaper_trend()
    elif func == "baby_diaper_trend_today":
        Baby(job).diaper_trend_today()
    elif func == "baby_weight":
        Baby(job).weight()
    elif func == "baby_weight_trend":
        Baby(job).weight_trend()
    elif func == "mom_pump":
        Baby(job).pump()

    else:
        log(error_code=40005)

        # log(str(task.chat_id) + ' - Calling Function: ' + task.function)

        # func = getattr(self, task.function)
        # func()

        time.sleep(1)


def check_running_tasks():
    for thread in list(running_tasks.keys()):
        if not running_tasks[thread].is_alive():
            running_tasks.pop(thread, None)
