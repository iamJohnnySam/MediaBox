import multiprocessing
import threading
import time

from common_workspace import message_queue, global_var
from communication_handler.socket import socket_main
from communication_handler.telegram import telegram_main
from shared_models import configuration
from shared_models.message import Message
from shared_tools.logger import log

t_telegram = None
t_socket = None


def start_thread_telegram():
    global t_telegram
    if t_telegram is None or not t_telegram.isAlive():
        t_telegram = threading.Thread(target=telegram_main.main, args=(), daemon=True)
        t_telegram.start()


def start_thread_socket():
    global t_socket
    if t_socket is None or not t_socket.isAlive():
        t_socket = threading.Thread(target=socket_main.main, args=(), daemon=True)
        t_socket.start()


def loop():
    pass


def main(flag_stop: multiprocessing.Value):
    global_var.flag_stop = flag_stop

    config = configuration.Configuration()
    telegram_avail = True if config.is_module_available("telegram") else False
    socket_avail = True if config.is_module_available("socket") else False

    log(msg="Communication Process is Ready...")
    message_queue.add_message(Message(f"--- iamJohnnySam ---\n{global_var.version}\n\n"
                                      f"Program Started on {config.host}..."))

    while not global_var.flag_stop.value:
        loop()
        time.sleep(1)

    flag_stop.value = global_var.flag_stop


if __name__ == "__main__":
    main(multiprocessing.Value('i', 0))
