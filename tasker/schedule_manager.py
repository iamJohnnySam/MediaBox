import threading
import time

import global_var
from record import logger
from tasker import scheduler


def run_schedule_manager():
    t_scheduler = threading.Thread(target=scheduler.run_scheduler)
    t_scheduler.start()
    logger.log(msg="Thread Started: Scheduler")

    # todo create default schedule tasks

    while t_scheduler.is_alive() and not global_var.stop_all:
        scheduler.check_running_threads()
        time.sleep(10)


    global_var.stop_all = True
