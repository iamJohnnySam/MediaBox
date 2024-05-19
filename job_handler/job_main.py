import threading
import time

from common_workspace import global_var, queues
from job_handler import queue_manager, schedule_manager
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

    log(msg="Job Process is Starting...")

    _ = configuration.Configuration()

    t_task = threading.Thread(target=queue_manager.run_task_mgr)
    t_task.start()
    t_schedule = threading.Thread(target=schedule_manager.run_scheduler)
    t_schedule.start()

    while not global_var.flag_stop.value:
        if not t_task.is_alive():
            t_task.join()
            t_task.run()
            log(msg="Thread Started: Task Manager")

        if not t_schedule.is_alive():
            t_schedule.join()
            t_schedule.run()
            log(msg="Thread Started: Schedule Manager")

        time.sleep(60)

    # todo backup_sequence(Job(function="backup_all"))


if __name__ == "__main__":
    main(queues.message_q, queues.job_q, queues.packet_q, queues.info_q,
         global_var.flag_stop, global_var.flag_restart, global_var.flag_reboot)
