import os
import sys
import threading
import time

from tools import start_up, params
from brains.job import Job
from brains.queue_manager import backup_sequence
from communication import channels
from communication.message import Message
import global_variables
from brains import schedule_manager, queue_manager
from tools.logger import log
from web import web_app

start_up.print_logo()
log(msg=f"Running {global_variables.system} on {global_variables.platform}. Host: {global_variables.host}")

t_task = threading.Thread(target=queue_manager.run_task_manager)
t_task.start()
log(msg="Thread Started: Task Manager")

t_schedule = threading.Thread(target=schedule_manager.run_schedule_manager)
t_schedule.start()
log(msg="Thread Started: Schedule Manager")

if params.is_module_available('telepot'):
    channels.init_channel()

if params.is_module_available('web'):
    t_webapp = threading.Thread(target=web_app.run_webapp, daemon=True)
    t_webapp.start()
    log(msg="Thread Started: Web app")

global_variables.ready_to_run = True
log(msg="Ready to Run...")
channels.send_message(Message("--- iamJohnnySam ---\n"
                              "Version 2.1\n\n"
                              f"Program Started on {global_variables.host}..."))

t_task.join()
crashed = True if not global_variables.stop_all else False
global_variables.stop_all = True

t_schedule.join()
log(msg="All threads merged")

backup_sequence(Job(function="backup_all"))

# ------ EXIT CONDITIONS -----------
if not global_variables.stop_all or crashed:
    channels.send_message(Message("Crashed."))
    time.sleep(60)

if (not global_variables.stop_all) or global_variables.restart:
    log(msg="argv was " + str(sys.argv))
    log(msg="sys.executable was " + str(sys.executable))
    start_up.keep_gap()
    start_up.print_logo()

    python = sys.executable
    os.execv(sys.executable, ['python'] + sys.argv)

else:
    if global_variables.reboot_pi:
        channels.send_message(Message("Rebooting now..."))
        log(msg="Rebooting now...")
        os.system("sudo reboot")

    else:
        channels.send_message(Message("Exiting..."))
        log(msg="CLEAN EXIT")
