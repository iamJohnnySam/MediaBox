import os
import platform
import sys
import threading
import time

import logger
import global_var
from communication import communicator
from maintenance import start_up
from scheduler import scheduler
from web import web_app

# CHECK RUNNING SYSTEM
logger.log("Currently running code on: " + platform.machine())

if platform.machine() == 'armv7l':
    logger.log("Program Started in Full Mode")
    global_var.ready_to_run = True

    t_scheduler = threading.Thread(target=scheduler.run_scheduler)
    t_scheduler.start()
    logger.log("Thread Started: Scheduler")

    t_webapp = threading.Thread(target=web_app.run_webapp, daemon=True)
    t_webapp.start()
    logger.log("Thread Started: Web app")

    # t_scheduler.join()
    while t_scheduler.is_alive():
        scheduler.check_running_threads()
        time.sleep(10)

else:
    logger.log("Code Running in Partial Mode")

    if True:
        t_webapp = threading.Thread(target=web_app.run_webapp)
        t_webapp.start()
        logger.log("Thread Started: Web app")

    t_webapp.join()

global_var.backup.run_code()

# ------ EXIT CONDITIONS -----------
if not global_var.stop_all:
    communicator.send_to_master("main", "Crashed.")
    time.sleep(60)

if (not global_var.stop_all) or global_var.restart:
    logger.log("argv was " + str(sys.argv))
    logger.log("sys.executable was " + str(sys.executable))
    logger.log("Restarting application now...")
    start_up.keep_gap()
    start_up.print_logo()

    python = sys.executable
    os.execv(sys.executable, ['python'] + sys.argv)

else:
    communicator.send_to_master("main", "Exiting...")
    logger.log("CLEAN EXIT")

    if global_var.reboot_pi:
        logger.log("Rebooting Pi now...")
        os.system("sudo reboot")
