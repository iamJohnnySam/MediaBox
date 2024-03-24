import threading
import time

import global_variables
from brains import task_queue
from brains.job import Job
from modules.admin import Admin
from modules.baby import Baby
from modules.movie_finder import MovieFinder
from modules.transmission import Transmission
from tools.logger import log


def run_task_manager():
    while not global_variables.ready_to_run:
        time.sleep(5)

    log(msg="Task Manager Started")

    while not global_variables.stop_all:
        while not task_queue.job_q.empty():
            job: Job = task_queue.get_job()
            threading.Thread(target=run_task, args=(job,)).start()


def run_task(job: Job):
    func = job.function
    if func == "alive":
        Admin(job).alive()
    elif func == "time":
        Admin(job).time()
    elif func == "help":
        Admin(job).help()

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
