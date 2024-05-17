import threading
from queue import Queue

msg_q = Queue(maxsize=0)
msg_lock = threading.Lock()


def add_message(msg):
    global msg_q
    with msg_lock:
        msg_q.put(msg)


def get_message():
    global msg_q
    with msg_lock:
        msg = msg_q.get()
    return msg
