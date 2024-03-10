import os
import platform
import sys
import threading
import time

from communication import channels
from tools import logger
import global_var
from communication import communicator
from maintenance import start_up
from modules import backup
from tasker import task_manager, schedule_manager
from web import web_app

if platform.machine() == 'armv7l':
    logger.log(msg="Program Started of Raspberry Pi in Operation Mode")
    operation_mode = True
else:
    logger.log(msg="Code Running in Testing mode on: " + platform.machine())
    operation_mode = False

if operation_mode:
    channels.init_channel('all')
else:
    channels.init_channel('spark')

"""Starting Task Manager as a Thread"""
t_task = threading.Thread(target=task_manager.run_task_manager)
t_task.start()
logger.log(msg="Thread Started: Task Manager")

"""Starting Web Server as a Thread
Daemon Thread = True. If task manager fails program will reboot"""
t_webapp = threading.Thread(target=web_app.run_webapp, daemon=True)
t_webapp.start()
logger.log(msg="Thread Started: Web app")

t_schedule = threading.Thread(target=schedule_manager.run_schedule_manager)
t_schedule.start()

t_task.join()
global_var.stop_all = True

t_schedule.join()

# todo manual backup task
# backup.backup.run_code()

# ------ EXIT CONDITIONS -----------
if not global_var.stop_all:
    communicator.send_to_master("main", "Crashed.")
    time.sleep(60)

if (not global_var.stop_all) or global_var.restart:
    logger.log(msg="argv was " + str(sys.argv))
    logger.log(msg="sys.executable was " + str(sys.executable))
    logger.log(msg="Restarting application now...")
    start_up.keep_gap()
    start_up.print_logo()

    python = sys.executable
    os.execv(sys.executable, ['python'] + sys.argv)

else:
    communicator.send_to_master("main", "Exiting...")
    logger.log(msg="CLEAN EXIT")

    if global_var.reboot_pi:
        logger.log(msg="Rebooting Pi now...")
        os.system("sudo reboot")
