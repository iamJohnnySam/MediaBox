import logger
from communication.message import Message
from tasker.task import Task


class TaskMessage(Task):
    def __init__(self, task: Message):
        super().__init__(task.telepot_account)
        logger.log(str(task.chat_id) + ' - Calling Function: ' + task.function)

        func = getattr(self, task.function)
        func()
