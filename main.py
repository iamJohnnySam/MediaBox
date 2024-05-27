import multiprocessing
import os
import sys
import time

from shared_tools import start_up
from common_workspace import global_var, queues
from communication_handler import communication_main
from job_handler import job_main
from shared_models import configuration
from shared_models.message import Message
from web_handler import web_main
from shared_tools.logger import log

crashed = False


def main():
    global crashed

    config = configuration.Configuration()
    log(msg=f"Running {config.system} on {config.machine}. Host: {config.host}")

    p_communicator = multiprocessing.Process(target=communication_main.main,
                                             daemon=True,
                                             args=(queues.message_q,
                                                   queues.job_q,
                                                   queues.packet_q,
                                                   queues.info_q,
                                                   global_var.flag_stop,
                                                   global_var.flag_restart,
                                                   global_var.flag_reboot))
    p_communicator.start()
    log(msg="Process Started: Communication Handler")

    p_tasker = multiprocessing.Process(target=job_main.main,
                                       args=(queues.message_q,
                                             queues.job_q,
                                             queues.packet_q,
                                             queues.info_q,
                                             global_var.flag_stop,
                                             global_var.flag_restart,
                                             global_var.flag_reboot))
    p_tasker.start()
    log(msg="Process Started: Job Handler")

    p_web = multiprocessing.Process(target=web_main.main,
                                    daemon=True,
                                    args=(queues.message_q,
                                          queues.job_q,
                                          queues.packet_q,
                                          queues.info_q,
                                          global_var.flag_stop,
                                          global_var.flag_restart,
                                          global_var.flag_reboot))
    p_web.start()
    log(msg="Process Started: Web Handler")

    queues.message_q.put(Message(f"--- iamJohnnySam ---\n{global_var.version}\n\n"
                                 f"Program Started on {config.host}..."))

    p_tasker.join()
    log(msg="Process Ended: Job Handler")

    crashed = True if not global_var.flag_stop.value else False
    global_var.flag_stop.value = True

    p_web.join()
    log(msg="Process Ended: Web Handler")


def exit_program():
    if not global_var.flag_stop.value or crashed:
        queues.message_q.put(Message("Crashed."))
        time.sleep(60)

    if (not global_var.flag_stop.value) or global_var.flag_restart.value:
        log(msg="argv was " + str(sys.argv))
        log(msg="sys.executable was " + str(sys.executable))
        start_up.keep_gap()
        start_up.print_logo()

        _ = sys.executable
        os.execv(sys.executable, ['python'] + sys.argv)

    else:
        if global_var.flag_reboot.value:
            queues.message_q.put(Message("Rebooting now..."))
            log(msg="Rebooting now...")
            os.system("sudo reboot")

        else:
            queues.message_q.put(Message("Exiting..."))
            log(msg="CLEAN EXIT")


if __name__ == "__main__":
    start_up.print_logo()
    main()
    exit_program()
