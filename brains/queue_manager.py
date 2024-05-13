import threading
import time

import global_variables
import refs
from brains import task_queue
from brains.job import Job
from communication import channel_control
from modules.admin import Admin
from modules.baby import Baby
from modules.backup import BackUp
from modules.cctv_checker import CCTVChecker
from modules.finance import Finance
from modules.folder_refactor import RefactorFolder
from modules.movie_finder import MovieFinder
from modules.news_reader import NewsReader
from modules.show_downloader import ShowDownloader
from modules.subscriptions import Subscriptions
from modules.transmission import Transmission
from tools import params
from shared_tools.logger import log

running_tasks = {}


def run_task_mgr():
    while not global_variables.ready:
        time.sleep(1)

    log(msg="Task Manager Started")

    while not global_variables.stop_all:
        while not task_queue.job_q.empty():
            job: Job = task_queue.get_job()

            check_running_tasks()

            if job.job_id in running_tasks.keys():
                log(job.job_id, "Waiting for Job to complete to process next task")
                task_queue.add_job(job)
                continue

            if job.job_id != 0:
                running_tasks[job.job_id] = threading.Thread(target=run_task, args=(job,))
                running_tasks[job.job_id].start()
            else:
                threading.Thread(target=run_task, args=(job,)).start()

        time.sleep(1)


def run_task(job: Job):
    # todo command dictionary
    job.update_job()
    func = job.function
    if func == "alive":
        Admin(job).alive()
    elif func == "time":
        Admin(job).time()
    elif func == "help":
        Admin(job).help()

    elif func == "backup_all":
        backup_sequence(job)
    elif func == "backup_database":
        backup = BackUp(job)
        backup.cp_all_databases()

    elif func == "check_shows":
        module = "media"
        if params.is_module_available(module):
            ShowDownloader(job).check_shows()
        else:
            channel_control.send_to_network(job, module)
    elif func == "find_movie":
        MovieFinder(job).find_movie()

    elif func == "check_news":
        NewsReader(job).get_news()
    elif func == "check_news_all":
        NewsReader(job).get_news_all()
    elif func == "show_subs_news":
        job.function = "check_news"
        NewsReader(job).get_news()
    elif func == "show_news":
        NewsReader(job).show_news_channels()
    elif func == "subs_news":
        NewsReader(job).subscribe()

    elif func == "check_cctv":
        module = "cctv"
        if params.is_module_available(module):
            cctv = CCTVChecker(job)
            cctv.download_cctv()
            cctv.clean_up()
        else:
            channel_control.send_to_network(job, module)
    elif func == "get_cctv":
        module = "cctv"
        if params.is_module_available(module):
            cctv = CCTVChecker(job)
            cctv.download_cctv()
            cctv.get_last(10)
            cctv.clean_up()
        else:
            channel_control.send_to_network(job, module)
    elif func == "add_me_to_cctv":
        Subscriptions(job).manage_chat_group("cctv")
    elif func == "remove_me_from_cctv":
        Subscriptions(job).manage_chat_group("cctv", add=False, remove=True)

    elif func == "list_torrents":
        module = "media"
        if params.is_module_available(module):
            Transmission(job).send_list()
        else:
            channel_control.send_to_network(job, module)
    elif func == "clean_up_downloads":
        module = "media"
        if params.is_module_available(module):
            log(job.job_id, "Starting Transmission Cleanup")
            torrent = Transmission(job)
            torrent.delete_downloaded()
            torrent.list_torrents()
            log(job.job_id, "Starting Downloads Refactor")
            RefactorFolder(job).clean_torrent_downloads()
            log(job.job_id, "Cleanup sequence Complete")
        else:
            channel_control.send_to_network(job, module)

    elif func == "finance":
        Finance(job).finance()
    elif func == "sms_bill":
        Finance(job).sms()

    elif func == "baby_feed":
        Baby(job).feed()
    elif func == "baby_feed_history":
        Baby(job).feed_history()
    elif func == "baby_feed_trend":
        Baby(job).feed_trend()
    elif func == "baby_feed_trend_today":
        Baby(job).feed_trend_today()
    elif func == "baby_diaper":
        Baby(job).diaper()
    elif func == "baby_diaper_history":
        Baby(job).diaper_history()
    elif func == "baby_diaper_trend":
        Baby(job).diaper_trend()
    elif func == "baby_diaper_trend_today":
        Baby(job).diaper_trend_today()
    elif func == "baby_weight":
        Baby(job).weight()
    elif func == "baby_weight_trend":
        Baby(job).weight_trend()
    elif func == "mom_pump":
        Baby(job).pump()
    elif func == "add_me_to_baby":
        Subscriptions(job).manage_chat_group("baby")
    elif func == "remove_me_from_baby":
        Subscriptions(job).manage_chat_group("baby", add=False, remove=True)

    elif func == "start_over":
        Admin(job).start_over()
    elif func == "exit_all":
        Admin(job).exit_all()
        channel_control.inform_network(job)
    elif func == "reboot_pi":
        Admin(job).reboot_pi()

    # todo edit message
    # todo add class variable in each module to state the format of the collection set

    else:
        log(error_code=40005)

        # log(str(task.chat_id) + ' - Calling Function: ' + task.function)
        # func = getattr(self, task.function)
        # func()

        time.sleep(1)


def check_running_tasks():
    for thread in list(running_tasks.keys()):
        if not running_tasks[thread].is_alive():
            running_tasks.pop(thread, None)


def backup_sequence(job: Job):
    backup = BackUp(job)
    backup.move_folders.append(refs.logs_location)
    backup.move_png_files.append(refs.charts_save_location)
    backup.copy_files.append(refs.password_file)
    backup.move_files.append(refs.terminal_output)
    backup.databases.append(refs.db_admin)
    backup.databases.append(refs.db_news)
    backup.databases.append(refs.db_finance)
    backup.databases.append(refs.db_baby)
    backup.databases.append(refs.db_entertainment)
    backup.run_backup()

    # todo move to task creation
    # backup.backup.copy_files.append(telepot_accounts)
    # backup.backup.copy_folders.append(telepot_commands)
    # backup.backup.copy_folders.append(telepot_callback_database)

    # todo move to task creation
    # backup.backup.move_folders.append(telepot_image_dump)

    # todo move to task creation
    # backup.backup.move_folders_common.append(finance_images)
