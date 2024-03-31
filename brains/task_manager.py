import threading
import time

import global_variables
import refs
from brains import task_queue
from brains.job import Job
from modules.admin import Admin
from modules.baby import Baby
from modules.backup import BackUp
from modules.cctv_checker import CCTVChecker
from modules.folder_refactor import RefactorFolder
from modules.movie_finder import MovieFinder
from modules.news_reader import NewsReader
from modules.show_downloader import ShowDownloader
from modules.transmission import Transmission
from tools.logger import log

running_tasks = {}


def run_task_manager():
    while not global_variables.ready_to_run:
        time.sleep(5)

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
    job.update_job()
    func = job.function
    if func == "alive":
        Admin(job).alive()
    elif func == "time":
        Admin(job).time()
    elif func == "help":
        Admin(job).help()
    elif func == "backup_all":
        backup = BackUp(job, refs.backup_location)
        backup.move_folders.append(refs.logs_location)
        backup.move_png_files.append(refs.charts_save_location)
        backup.copy_files.append(refs.password_file)
        backup.move_files.append(refs.terminal_output)
        backup.run_backup()
    elif func == "backup_database":
        backup = BackUp(job, refs.backup_location)
        backup.cp_databases()

    elif func == "check_shows":
        ShowDownloader(job).check_shows()
    elif func == "find_movie":
        MovieFinder(job).find_movie()
    elif func == "request_tv_show":
        pass

    elif func == "check_news":
        NewsReader(job).get_news()
    elif func == "check_news_all":
        NewsReader(job).get_news_all()
    elif func == "subscribe_news":
        pass
    elif func == "add_me_to_news":
        pass
    elif func == "remove_me_from_news":
        pass

    elif func == "check_cctv":
        cctv = CCTVChecker(job)
        cctv.download_cctv()
        cctv.get_last(10)
        cctv.clean_up()
    elif func == "add_me_to_cctv":
        pass
    elif func == "remove_me_from_cctv":
        pass

    elif func == "list_torrents":
        Transmission(job).send_list()
    elif func == "clean_up_downloads":
        log(job.job_id, "Starting Transmission Cleanup")
        torrent = Transmission(job)
        torrent.delete_downloaded()
        torrent.list_torrents()
        log(job.job_id, "Starting Downloads Refactor")
        RefactorFolder(job, refs.torrent_download).clean_torrent_downloads()
        log(job.job_id, "Cleanup sequence Complete")

    elif func == "finance":
        pass
    elif func == "sms_bill":
        pass

    elif func == "add_me_to_baby":
        pass
    elif func == "remove_me_from_baby":
        pass
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
