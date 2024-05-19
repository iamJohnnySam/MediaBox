import multiprocessing
import time

from common_workspace import global_var, queues
from communication_handler.socket.network_server import Server
from communication_handler.telegram.initialize_telegram import init_telegram
from shared_models import configuration
from shared_tools.logger import log


def main(message_q, job_q, packet_q, info_q, flag_stop, flag_restart, flag_reboot):
    queues.message_q = message_q
    queues.job_q = job_q
    queues.packet_q = packet_q
    queues.info_q = info_q
    global_var.flag_stop = flag_stop
    global_var.flag_restart = flag_restart
    global_var.flag_reboot = flag_reboot

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
