from job_handler.modules.admin import Admin
from job_handler.modules.baby import Baby
from job_handler.modules.backup import BackUp
from job_handler.modules.cctv_checker import CCTVChecker
from job_handler.modules.finance import Finance
from job_handler.modules.folder_refactor import RefactorFolder
from job_handler.modules.movie_finder import MovieFinder
from job_handler.modules.news_reader import NewsReader
from job_handler.modules.show_downloader import ShowDownloader
from job_handler.modules.subscriptions import Subscriptions
from job_handler.modules.transmission import Transmission
from shared_models import configuration
from shared_models.job import Job
from shared_tools.logger import log


class Sequence:
    def __init__(self, job: Job):
        self.job = job
        log(job_id=self.job.job_id, msg=f"{self.job.chat_id} - Calling Function: {self.job.function}")
        func = getattr(self, self.job.function)
        try:
            func()
        except AttributeError:
            log(error_code=40005, job_id=self.job.job_id)

    def send_to_network(self):
        # todo
        pass

    def send_to_everyone(self):
        # todo
        pass

    def alive(self):
        Admin(self.job).alive()

    def time(self):
        Admin(self.job).time()

    def help(self):
        Admin(self.job).help()

    def backup_all(self):
        backup = BackUp(self.job)
        config = configuration.Configuration()

        backup.move_folders.append(config.admin["log_location"])
        backup.copy_files.append('passwords.py')
        for database in config.admin["backup_databases"]:
            backup.databases.append(database)
        backup.run_backup()

        # todo move to task creation
        # backup.backup.copy_files.append(telepot_accounts)
        # backup.backup.copy_folders.append(telepot_commands)
        # backup.backup.copy_folders.append(telepot_callback_database)

        # todo move to task creation
        # backup.backup.move_folders.append(telepot_image_dump)

        # todo move to task creation
        # backup.backup.move_folders_common.append(finance_images)

    def backup_database(self):
        backup = BackUp(self.job)
        for database in configuration.Configuration().admin["backup_databases"]:
            backup.databases.append(database)
        backup.cp_all_databases()

    def check_shows(self):
        if configuration.Configuration.media == {}:
            self.send_to_network()
        else:
            ShowDownloader(self.job).check_shows()

    def find_movie(self):
        MovieFinder(self.job).find_movie()

    def check_news(self):
        if configuration.Configuration.news == {}:
            self.send_to_network()
        else:
            NewsReader(self.job).get_news()

    def check_news_all(self):
        if configuration.Configuration.news == {}:
            self.send_to_network()
        else:
            NewsReader(self.job).get_news_all()

    def show_subs_news(self):
        if configuration.Configuration.news == {}:
            self.send_to_network()
        else:
            self.job.function = "check_news"
            NewsReader(self.job).get_news()

    def show_news(self):
        if configuration.Configuration.news == {}:
            self.send_to_network()
        else:
            NewsReader(self.job).show_news_channels()

    def subs_news(self):
        if configuration.Configuration.news == {}:
            self.send_to_network()
        else:
            NewsReader(self.job).subscribe()

    def check_cctv(self):
        if configuration.Configuration.cctv == {}:
            self.send_to_network()
        else:
            cctv = CCTVChecker(self.job)
            cctv.download_cctv()
            cctv.clean_up()

    def get_cctv(self):
        if configuration.Configuration.cctv == {}:
            self.send_to_network()
        else:
            cctv = CCTVChecker(self.job)
            cctv.download_cctv()
            cctv.get_last(10)
            cctv.clean_up()

    def add_me_to_cctv(self):
        Subscriptions(self.job).manage_chat_group("cctv")

    def remove_me_from_cctv(self):
        Subscriptions(self.job).manage_chat_group("cctv", add=False, remove=True)

    def list_torrents(self):
        if configuration.Configuration.media == {}:
            self.send_to_network()
        else:
            Transmission(self.job).send_list()

    def clean_up_downloads(self):
        if configuration.Configuration.media == {}:
            self.send_to_network()
        else:
            log(self.job.job_id, "Starting Transmission Cleanup")
            torrent = Transmission(self.job)
            torrent.delete_downloaded()
            torrent.list_torrents()
            log(self.job.job_id, "Starting Downloads Refactor")
            RefactorFolder(self.job).clean_torrent_downloads()
            log(self.job.job_id, "Cleanup sequence Complete")

    def finance(self):
        if configuration.Configuration.finance == {}:
            self.send_to_network()
        else:
            Finance(self.job).finance()

    def sms_bill(self):
        if configuration.Configuration.finance == {}:
            self.send_to_network()
        else:
            Finance(self.job).sms()

    def baby_feed(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).feed()

    def baby_feed_history(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).feed_history()

    def baby_feed_trend(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).feed_trend()

    def baby_feed_trend_today(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).feed_trend_today()

    def baby_diaper(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).diaper()

    def baby_diaper_history(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).diaper_history()

    def baby_diaper_trend(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).diaper_trend()

    def baby_diaper_trend_today(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).diaper_trend_today()

    def baby_weight(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).weight()

    def baby_weight_trend(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).weight_trend()

    def mom_pump(self):
        if configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Baby(self.job).pump()

    def add_me_to_baby(self):
        if configuration.Configuration.telegram == {} or configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Subscriptions(self.job).manage_chat_group("baby")

    def remove_me_from_baby(self):
        if configuration.Configuration.telegram == {} or configuration.Configuration.baby == {}:
            self.send_to_network()
        else:
            Subscriptions(self.job).manage_chat_group("baby", add=False, remove=True)

    def start_over(self):
        Admin(self.job).start_over()

    def exit_all(self):
        Admin(self.job).exit_all()
        self.send_to_everyone()

    def reboot_pi(self):
        Admin(self.job).reboot_pi()
