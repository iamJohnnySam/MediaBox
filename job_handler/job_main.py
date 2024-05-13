def main(flag_stop):
    t_task = threading.Thread(target=queue_manager.run_task_mgr)
    t_task.start()
    log(msg="Thread Started: Task Manager")

    t_schedule = threading.Thread(target=schedule_manager.run_scheduler)
    t_schedule.start()
    log(msg="Thread Started: Schedule Manager")



backup_sequence(Job(function="backup_all"))