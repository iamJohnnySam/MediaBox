import threading
from queue import Queue

from communication.message import Message
from modules.base_module import Job

job_q = Queue(maxsize=0)
msg_q = Queue(maxsize=0)
lock = threading.Lock()


def add_job(job: Job):
    global job_q
    with lock:
        job_q.put(job)


def get_job() -> Job:
    global job_q
    with lock:
        job = job_q.get()
    return job


def add_message(msg: Message):
    global job_q
    with lock:
        job_q.put(msg)


def get_message() -> Message:
    global job_q
    with lock:
        job = job_q.get()
    return job
