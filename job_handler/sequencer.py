from common_workspace import queues
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
from shared_models.message import Message
from shared_tools.configuration_tools import is_config_enabled
from shared_tools.custom_exceptions import UnexpectedOperation
from shared_tools.logger import log


class Sequence:
    def __init__(self, job: Job):
        self.job = job
        self.config = configuration.Configuration()

        if not self.check_module_availability():
            log(job_id=self.job.job_id, msg="Sending job to network.")
            queues.packet_q.put(self.job.job_compress())
            return

        log(job_id=self.job.job_id, msg=f"{self.job.chat_id} - Calling Function: {self.job.function}")
        try:
            func = getattr(self, self.job.function)
        except AttributeError:
            log(error_code=40005, job_id=self.job.job_id)
            return
        func()

    def check_module_availability(self):
        if self.job.module == "":
            return True
        elif self.job.module == "media":
            return is_config_enabled(self.config.media)
        elif self.job.module == "news":
            return is_config_enabled(self.config.news)
        elif self.job.module == "cctv":
            return is_config_enabled(self.config.cctv)
        elif self.job.module == "telegram":
            return is_config_enabled(self.config.telegram)
        elif self.job.module == "finance":
            return is_config_enabled(self.config.finance)
        elif self.job.module == "baby":
            return is_config_enabled(self.config.baby)

        log(error_code=40003)
        return UnexpectedOperation

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
        ShowDownloader(self.job).check_shows()

    def find_movie(self):
        MovieFinder(self.job).find_movie()

    def check_news(self):
        NewsReader(self.job).get_news()

    def check_news_all(self):
        NewsReader(self.job).get_news_all()

    def show_subs_news(self):
        self.job.function = "check_news"
        NewsReader(self.job).get_news()

    def show_news(self):
        NewsReader(self.job).show_news_channels()

    def subs_news(self):
        NewsReader(self.job).subscribe()

    def check_cctv(self):
        cctv = CCTVChecker(self.job)
        cctv.download_cctv()
        cctv.clean_up(self.config.cctv["sent"])
        queues.message_q.put(Message("CCTV Check Completed", job=self.job))

    def get_cctv(self):
        cctv = CCTVChecker(self.job)
        cctv.download_cctv()
        cctv.get_last(10)
        cctv.clean_up(self.config.cctv["sent"])

    def add_me_to_cctv(self):
        # todo check if connected to the correct telegram
        Subscriptions(self.job).manage_chat_group("cctv")

    def remove_me_from_cctv(self):
        # todo check if connected to the correct telegram
        Subscriptions(self.job).manage_chat_group("cctv", add=False, remove=True)

    def list_torrents(self):
        Transmission(self.job).send_list()

    def clean_up_downloads(self):
        log(self.job.job_id, "Starting Transmission Cleanup")
        torrent = Transmission(self.job)
        torrent.delete_downloaded()
        torrent.list_torrents()
        log(self.job.job_id, "Starting Downloads Refactor")
        RefactorFolder(self.job).clean_torrent_downloads()
        log(self.job.job_id, "Cleanup sequence Complete")

    def finance(self):
        Finance(self.job).finance()

    def sms_bill(self):
        Finance(self.job).sms()

    def baby_feed(self):
        Baby(self.job).feed()

    def baby_feed_history(self):
        Baby(self.job).feed_history()

    def baby_feed_trend(self):
        Baby(self.job).feed_trend()

    def baby_feed_trend_today(self):
        Baby(self.job).feed_trend_today()

    def baby_diaper(self):
        Baby(self.job).diaper()

    def baby_diaper_history(self):
        Baby(self.job).diaper_history()

    def baby_diaper_trend(self):
        Baby(self.job).diaper_trend()

    def baby_diaper_trend_today(self):
        Baby(self.job).diaper_trend_today()

    def baby_weight(self):
        Baby(self.job).weight()

    def baby_weight_trend(self):
        Baby(self.job).weight_trend()

    def mom_pump(self):
        Baby(self.job).pump()

    def add_me_to_baby(self):
        # todo check if connected to the correct telegram
        Subscriptions(self.job).manage_chat_group("baby")

    def remove_me_from_baby(self):
        # todo check if connected to the correct telegram
        Subscriptions(self.job).manage_chat_group("baby", add=False, remove=True)

    def start_over(self):
        Admin(self.job).start_over()

    def exit_all(self):
        Admin(self.job).exit_all()
        self.send_to_everyone()

    def reboot_pi(self):
        Admin(self.job).reboot_pi()
