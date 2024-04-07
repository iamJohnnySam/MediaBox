import os
import sys
import threading
import time

import refs
from brains.job import Job
from brains.queue_manager import backup_sequence
from communication import channels
from communication.message import Message
from tools import logger, start_up
import global_variables
from brains import schedule_manager, queue_manager
from web import web_app

if global_variables.operation_mode:
    logger.log(msg="Program Started on Raspberry Pi in Operation Mode")
    channels.init_channel('all')
else:
    logger.log(msg="Code Running in Testing mode on: " + global_variables.platform)
    channels.init_channel(refs.main_channel)

t_task = threading.Thread(target=queue_manager.run_task_manager)
t_task.start()
logger.log(msg="Thread Started: Task Manager")

t_schedule = threading.Thread(target=schedule_manager.run_schedule_manager)
t_schedule.start()
logger.log(msg="Thread Started: Schedule Manager")

t_webapp = threading.Thread(target=web_app.run_webapp, daemon=True)
t_webapp.start()
logger.log(msg="Thread Started: Web app")

global_variables.ready_to_run = True
logger.log(msg="Ready to Run...")
channels.channels[refs.main_channel].send_now(Message("- iamJohnnySam -\n"
                                                      "Version 2.0\n\n"
                                                      "Program Started"))

t_task.join()
global_variables.stop_all = True
t_schedule.join()
logger.log(msg="All threads merged")

backup_sequence(Job(function="backup_all"))

# ------ EXIT CONDITIONS -----------
if not global_variables.stop_all:
    channels.channels[refs.main_channel].send_now(Message("Crashed."))
    time.sleep(60)

if (not global_variables.stop_all) or global_variables.restart:
    logger.log(msg="argv was " + str(sys.argv))
    logger.log(msg="sys.executable was " + str(sys.executable))
    logger.log(msg="Restarting application now...")
    start_up.keep_gap()
    start_up.print_logo()

    python = sys.executable
    os.execv(sys.executable, ['python'] + sys.argv)

else:
    channels.channels[refs.main_channel].send_now(Message("Exiting..."))
    logger.log(msg="CLEAN EXIT")

    if global_variables.reboot_pi:
        logger.log(msg="Rebooting Pi now...")
        os.system("sudo reboot")
