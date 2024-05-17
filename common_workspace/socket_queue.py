import threading
from queue import Queue

msg_q = Queue(maxsize=0)
socket_lock = threading.Lock()


def add_message(msg):
    global msg_q
    with socket_lock:
        msg_q.put(msg)


def get_message():
    global msg_q
    with socket_lock:
        msg = msg_q.get()
    return msg
