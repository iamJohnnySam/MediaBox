import multiprocessing
import time

from common_workspace import global_var
from communication_handler.socket.network_server import Server
from communication_handler.telegram.initialize_telegram import init_telegram
from shared_models import configuration
from shared_tools.logger import log


def main(flag_stop: multiprocessing.Value):
    global_var.flag_stop = flag_stop
    log(msg="Communication Process is Starting...")

    config = configuration.Configuration()
    telepot_channels, main_channel = init_telegram(config.telegram)

    server_socket = Server(config.host, config.socket)

    while not global_var.flag_stop.value:
        # todo
        time.sleep(1)

    flag_stop.value = global_var.flag_stop


if __name__ == "__main__":
    main(multiprocessing.Value('i', 0))
