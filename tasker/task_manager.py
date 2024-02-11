import time

import global_var
from tasker import task_queue


def run_task_manager():
    while not global_var.ready_to_run:
        time.sleep(5)

    while not global_var.stop_all:
        if task_queue.msg_q.empty():
            # todo tasker handler
            pass
        time.sleep(1)
