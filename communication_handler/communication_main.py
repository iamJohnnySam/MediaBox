import threading

from common_workspace import global_var, queues
from communication_handler import message_manager, socket_manager
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

    t_telegram = threading.Thread(target=message_manager.run_telegram, daemon=True)
    t_telegram.start()

    t_socket = threading.Thread(target=socket_manager.run_sockets(), daemon=True)
    t_socket.start()

    t_telegram.join()
    t_socket.join()


if __name__ == "__main__":
    main(queues.message_q, queues.job_q, queues.packet_q, queues.info_q,
         global_var.flag_stop, global_var.flag_restart, global_var.flag_reboot)
