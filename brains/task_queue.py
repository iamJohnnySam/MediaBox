import threading
from queue import Queue

job_q = Queue(maxsize=0)
msg_q = Queue(maxsize=0)
lock = threading.Lock()


def add_job(job):
    global job_q
    with lock:
        job_q.put(job)


def get_job():
    global job_q
    with lock:
        job = job_q.get()
    return job


def add_message(msg):
    global job_q
    with lock:
        job_q.put(msg)


def get_message():
    global job_q
    with lock:
        job = job_q.get()
    return job
