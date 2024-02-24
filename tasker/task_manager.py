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


from logging import logger
from module.job import Job
from tasker.task import Task


class TaskMessage(Task):
    def __init__(self, task: Job):
        super().__init__(task.telepot_account)
        logger.log(str(task.chat_id) + ' - Calling Function: ' + task.function)

        func = getattr(self, task.function)
        func()
