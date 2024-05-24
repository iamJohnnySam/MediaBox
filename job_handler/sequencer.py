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
from shared_tools.configuration_tools import is_config_enabled
from shared_tools.logger import log


class Sequence:
    def __init__(self, job: Job):
        self.job = job
        self.config = configuration.Configuration()

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

    def no_function(self):
        # todo
        # self.send_now(Message("Chatbot Disabled. Type /help to find more information", job=msg))
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
        for database in self.config.admin["backup_databases"]:
            backup.databases.append(database)
        backup.cp_all_databases()

    def check_shows(self):
        if is_config_enabled(self.config.media):
            ShowDownloader(self.job).check_shows()
        else:
            self.send_to_network()

    def find_movie(self):
        MovieFinder(self.job).find_movie()

    def check_news(self):
        if is_config_enabled(self.config.news):
            NewsReader(self.job).get_news()
        else:
            self.send_to_network()

    def check_news_all(self):
        if is_config_enabled(self.config.news):
            NewsReader(self.job).get_news_all()
        else:
            self.send_to_network()

    def show_subs_news(self):
        if is_config_enabled(self.config.news):
            self.job.function = "check_news"
            NewsReader(self.job).get_news()
        else:
            self.send_to_network()

    def show_news(self):
        if is_config_enabled(self.config.news):
            NewsReader(self.job).show_news_channels()
        else:
            self.send_to_network()

    def subs_news(self):
        if is_config_enabled(self.config.news):
            NewsReader(self.job).subscribe()
        else:
            self.send_to_network()

    def check_cctv(self):
        if is_config_enabled(self.config.cctv):
            cctv = CCTVChecker(self.job)
            cctv.download_cctv()
            cctv.clean_up()
        else:
            self.send_to_network()

    def get_cctv(self):
        if is_config_enabled(self.config.cctv):
            cctv = CCTVChecker(self.job)
            cctv.download_cctv()
            cctv.get_last(10)
            cctv.clean_up()
        else:
            self.send_to_network()

    def add_me_to_cctv(self):
        if is_config_enabled(self.config.telegram):
            # todo check if connected to the correct telegram
            Subscriptions(self.job).manage_chat_group("cctv")
        else:
            self.send_to_network()

    def remove_me_from_cctv(self):
        if is_config_enabled(self.config.telegram):
            # todo check if connected to the correct telegram
            Subscriptions(self.job).manage_chat_group("cctv", add=False, remove=True)
        else:
            self.send_to_network()

    def list_torrents(self):
        if is_config_enabled(self.config.media):
            Transmission(self.job).send_list()
        else:
            self.send_to_network()

    def clean_up_downloads(self):
        if is_config_enabled(self.config.media):
            log(self.job.job_id, "Starting Transmission Cleanup")
            torrent = Transmission(self.job)
            torrent.delete_downloaded()
            torrent.list_torrents()
            log(self.job.job_id, "Starting Downloads Refactor")
            RefactorFolder(self.job).clean_torrent_downloads()
            log(self.job.job_id, "Cleanup sequence Complete")
        else:
            self.send_to_network()

    def finance(self):
        if is_config_enabled(self.config.finance):
            Finance(self.job).finance()
        else:
            self.send_to_network()

    def sms_bill(self):
        if is_config_enabled(self.config.finance):
            Finance(self.job).sms()
        else:
            self.send_to_network()

    def baby_feed(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).feed()
        else:
            self.send_to_network()

    def baby_feed_history(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).feed_history()
        else:
            self.send_to_network()

    def baby_feed_trend(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).feed_trend()
        else:
            self.send_to_network()

    def baby_feed_trend_today(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).feed_trend_today()
        else:
            self.send_to_network()

    def baby_diaper(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).diaper()
        else:
            self.send_to_network()

    def baby_diaper_history(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).diaper_history()
        else:
            self.send_to_network()

    def baby_diaper_trend(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).diaper_trend()
        else:
            self.send_to_network()

    def baby_diaper_trend_today(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).diaper_trend_today()
        else:
            self.send_to_network()

    def baby_weight(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).weight()
        else:
            self.send_to_network()

    def baby_weight_trend(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).weight_trend()
        else:
            self.send_to_network()

    def mom_pump(self):
        if is_config_enabled(self.config.baby):
            Baby(self.job).pump()
        else:
            self.send_to_network()

    def add_me_to_baby(self):
        if is_config_enabled(self.config.telegram):
            # todo check if connected to the correct telegram
            Subscriptions(self.job).manage_chat_group("baby")
        else:
            self.send_to_network()

    def remove_me_from_baby(self):
        if is_config_enabled(self.config.telegram):
            # todo check if connected to the correct telegram
            Subscriptions(self.job).manage_chat_group("baby", add=False, remove=True)
        else:
            self.send_to_network()

    def start_over(self):
        Admin(self.job).start_over()

    def exit_all(self):
        Admin(self.job).exit_all()
        self.send_to_everyone()

    def reboot_pi(self):
        Admin(self.job).reboot_pi()
