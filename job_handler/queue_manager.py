import threading
import time

from common_workspace import global_var, queues
from job_handler.sequencer import Sequence
from shared_models.job import Job
from shared_tools.logger import log

running_tasks = {}


def run_task_mgr():
    log(msg="Task Manager Started")

    while not global_var.flag_stop.value:
        while not queues.job_q.empty():
            job: Job = queues.job_q.get()

            check_running_tasks()

            if job.function in running_tasks.keys():
                log(job.job_id, "Waiting for Job to complete to process next task")
                queues.job_q.put(job)
                continue

            task_thread = threading.Thread(target=execute, args=(job,))
            running_tasks[job.function] = task_thread
            task_thread.start()

        time.sleep(1)


def execute(job: Job):
    Sequence(job)

# todo edit message
# todo add class variable in each module to state the format of the collection set


def check_running_tasks():
    for thread in list(running_tasks.keys()):
        if not running_tasks[thread].is_alive():
            running_tasks.pop(thread, None)
