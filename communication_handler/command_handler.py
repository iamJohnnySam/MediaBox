from common_workspace import queues
from communication_handler import communication_queues
from shared_models import configuration
from shared_models.job import Job
from shared_models.message import Message
from shared_tools.custom_exceptions import UnexpectedOperation
from shared_tools.message_tools import get_job_from_message, get_job_from_string, extract_job_from_callback
from shared_tools.logger import log


class Commander:
    def __init__(self, msg: dict | str, channel: str = None):
        self.job = None
        self.msg = msg
        self.channel = channel

        if self.channel is None:
            self.config = configuration.Configuration()
            self.channel = self.config.admin["main_telegram_channel"]

        if channel not in communication_queues.wait_queue.keys():
            communication_queues.wait_queue[channel] = {}

    def process_command(self):
        if type(self.msg) is dict:
            function, chat_id, username, reply_to, collection, photo = get_job_from_message(self.msg)
        elif type(self.msg) is str:
            username = "Console User"
            reply_to = 0
            chat_id = 0
            function, collection = get_job_from_string(self.msg)
        else:
            log(error_code=20019)
            return

        self.job = Job(function=function, channel=self.channel, chat_id=chat_id, username=username,
                       reply_to=reply_to, collection=collection)

        if self.job.function == "no_function":

            if self.job.chat_id in communication_queues.wait_queue[self.job.channel].keys():
                self._process_waiting_list()

            queues.job_q.put(self.job)
            log(job_id=self.job.job_id, error_code=30001)

        elif self.job.function == "cancel":
            if self.job.chat_id in communication_queues.wait_queue[self.job.channel].keys():
                func = communication_queues.wait_queue[self.job.channel][self.job.chat_id]["function"]
                log(msg=f"Job {func} canceled.")
                queues.message_q.put(Message(send_string=f"Job {func} canceled.", job=self.job))
                del communication_queues.wait_queue[self.job.channel][self.job.chat_id]
            else:
                log(msg=f"Nothing in the Queue")

        else:
            queues.job_q.put(self.job)
            log(job_id=self.job.job_id, msg=f"Job added {self.job.function} to queue.")

    def process_callback(self) -> (Job, str, bool):
        if type(self.msg) is dict:
            function, chat_id, username, reply_to, collection, index, value = extract_job_from_callback(self.msg)
        else:
            log(error_code=20019)
            raise UnexpectedOperation

        self.job = Job(function=function, channel=self.channel, chat_id=chat_id, username=username,
                       reply_to=reply_to, collection=collection)

        self.job.called_back = True

        get_val = False
        if value == '/CANCEL':
            reply = f'Cancelled! [{function}]'

        elif value == '/GET':
            self.get_user_input(index=index)
            reply = f'Type and send value! [{function}]'
            get_val = True

        else:
            try:
                self.job.collect(value=value, index=index)
                reply = f'Acknowledged! [{function}]'

            except ValueError as e:
                log(job_id=self.job.job_id, error_code=20004, error=str(e))
                reply = f'FAILED! (Error 20004) [{function}]'
                return self.job, reply, get_val

            except IndexError as e:
                log(job_id=self.job.job_id, error_code=20014, error=str(e))
                reply = f'FAILED! (Error 20014) [{function}]'
                return self.job, reply, get_val

            queues.job_q.put(self.job)

        return self.job, reply, get_val

    def _process_waiting_list(self):
        input_value = self.job.collection[0]

        queue_item = communication_queues.wait_queue[self.job.channel][self.job.chat_id]

        self.job.job_decompress(queue_item["job"])
        index = queue_item["index"]
        self.job.collect(input_value, index)
        self.job.called_back = True
        log(job_id=self.job.job_id, msg=f"Message recalled and job for {self.job.function} added to queue with "
                                        f"{input_value} collected at index {index}.")

        del communication_queues.wait_queue[self.job.channel][self.job.chat_id]

    def get_user_input(self, index=0):
        communication_queues.wait_queue[self.channel][self.job.chat_id] = {"job": self.job.job_compress(),
                                                                           "index": index}
        log(job_id=self.job.job_id, msg=f"Job queued and waiting input from {self.job.username} [{self.job.chat_id}]")
