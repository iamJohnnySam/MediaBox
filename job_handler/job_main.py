import threading
import time

from common_workspace import global_var
from job_handler import queue_manager, schedule_manager
from shared_models import configuration
from shared_tools.logger import log


def main(flag_stop):
    global_var.flag_stop = flag_stop
    log(msg="Job Process is Starting...")

    _ = configuration.Configuration()

    t_task = threading.Thread(target=queue_manager.run_task_mgr)
    t_schedule = threading.Thread(target=schedule_manager.run_scheduler)

    if not global_var.flag_stop.value:
        if not t_task.isAlive():
            t_task.start()
            log(msg="Thread Started: Task Manager")

        if not t_schedule.isAlive():
            t_schedule.start()
            log(msg="Thread Started: Schedule Manager")

        time.sleep(60)

    # todo backup_sequence(Job(function="backup_all"))
