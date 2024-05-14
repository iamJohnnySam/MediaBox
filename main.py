import multiprocessing
import os
import sys
import time

from communication_handler import communication_main
from job_handler import job_main
from web_handler import web_main
from shared_models.configuration import Configuration
from tools import start_up
from shared_tools.logger import log

flag_stop = multiprocessing.Value('i', 0)
flag_restart = multiprocessing.Value('i', 0)
flag_reboot = multiprocessing.Value('i', 0)
crashed = False


def main():
    global crashed
    config = Configuration()
    log(msg=f"Running {config.system} on {config.machine}. Host: {config.host}")

    p_communicator = multiprocessing.Process(target=communication_main.main,
                                             daemon=True,
                                             args=(flag_stop,))
    p_communicator.start()
    log(msg="Process Started: Communication Handler")

    p_tasker = multiprocessing.Process(target=job_main.main,
                                       args=(flag_stop, flag_restart, flag_reboot))
    p_tasker.start()
    log(msg="Process Started: Job Handler")

    p_web = multiprocessing.Process(target=web_main.main,
                                    daemon=True,
                                    args=(flag_stop,))
    p_web.start()
    log(msg="Process Started: Web Handler")

    p_tasker.join()
    log(msg="Process Ended: Job Handler")

    crashed = True if not flag_stop.value else False
    flag_stop.value = True

    p_web.join()
    log(msg="Process Ended: Web Handler")


def exit_program():
    if not flag_stop.value or crashed:
        channel_control.send_message(Message("Crashed."))
        time.sleep(60)

    if (not flag_stop.value) or flag_restart.value:
        log(msg="argv was " + str(sys.argv))
        log(msg="sys.executable was " + str(sys.executable))
        start_up.keep_gap()
        start_up.print_logo()

        _ = sys.executable
        os.execv(sys.executable, ['python'] + sys.argv)

    else:
        if flag_reboot.value:
            channel_control.send_message(Message("Rebooting now..."))
            log(msg="Rebooting now...")
            os.system("sudo reboot")

        else:
            channel_control.send_message(Message("Exiting..."))
            log(msg="CLEAN EXIT")


if __name__ == "__main__":
    start_up.print_logo()
    main()
    exit_program()
