import threading
from queue import Queue

from shared_tools.logger import log

job_q = Queue(maxsize=0)
job_lock = threading.Lock()


def add_job(job):
    global job_q
    with job_lock:
        job_q.put(job)
        log(job_id=job.job_id, msg="Job Added to Queue")


def get_job():
    global job_q
    with job_lock:
        job = job_q.get()
        log(job_id=job.job_id, msg="Job Removed from Queue")
    return job
