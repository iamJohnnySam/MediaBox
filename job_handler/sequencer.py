from common_workspace import queues
from job_handler.modules.admin import Admin
from job_handler.modules.baby import Baby
from job_handler.modules.backup import BackUp
from job_handler.modules.cctv_checker import CCTVChecker
from job_handler.modules.cloud import Cloud
from job_handler.modules.finance import Finance
from job_handler.modules.folder_refactor import RefactorFolder
from job_handler.modules.github import GitHub
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
from shared_tools.json_editor import JSONEditor
from shared_tools.logger import log
from shared_tools.packet_tools import packet_and_queue


class Sequence:
    def __init__(self, job: Job):
        self.job = job
        self.config = configuration.Configuration()

        self.function, self.module = self.check_command()
        if self.function == "":
            return

        if not self.check_module_availability():
            log(job_id=self.job.job_id, msg="Sending job to network.")
            packet_and_queue(self.job)
            return

        log(job_id=self.job.job_id, msg=f"{self.job.chat_id} - Calling Function: {self.function}")
        try:
            func = getattr(self, self.function)
        except AttributeError:
            log(error_code=40005, job_id=self.job.job_id)
            return
        func()

    def check_command(self) -> (str, str):
        commands = JSONEditor(self.config.commands["commands"]).read()

        if self.job.function not in commands.keys():
            queues.message_q.put(Message(f"Sorry {self.job.username}, that command is not known to me.\n"
                                         f"If you need help please send /help", job=self.job))
            return "", ""

        if type(commands[self.job.function]) is bool:
            queues.message_q.put(Message(send_string="That's not a command", job=self.job))
            log(job_id=self.job.job_id, error_code=30002)
            return "", ""

        cmd = commands[self.job.function]
        channel_is_not_main = self.job.channel not in self.config.telegram["accept_all_commands"]
        not_a_string = type(cmd) is not str
        channel_not_in_list = "bots" in cmd.keys() and self.job.channel not in cmd["bots"]
        not_all_bots = "all_bots" not in cmd.keys()
        not_bypass = not self.job.bypass_channel_check

        if not_bypass and channel_is_not_main and not_a_string and channel_not_in_list and not_all_bots:
            queues.message_q.put(Message(send_string=f"Command {self.job.function} does not work on this chatbot",
                                         job=self.job))
            log(job_id=self.job.job_id, error_code=30003)
            return "", ""

        log(job_id=self.job.job_id, msg="Command verification success.")

        if "module" in commands[self.job.function].keys():
            module = commands[self.job.function]["module"]
        else:
            module = "any"
        self.job.module = module

        if "function" in commands[self.job.function].keys():
            function = commands[self.job.function]["function"]
            log(job_id=self.job.job_id, msg=f"Function updated from {self.job.function} -> {function}")
        else:
            function = self.job.function
            log(job_id=self.job.job_id, msg="Function update not required.")

        return function, module

    def check_module_availability(self):
        if self.module == "any":
            return True
        elif self.module == "media":
            return is_config_enabled(self.config.media)
        elif self.module == "news":
            return is_config_enabled(self.config.news)
        elif self.module == "cctv":
            return is_config_enabled(self.config.cctv)
        elif self.module == "telegram":
            return is_config_enabled(self.config.telegram)
        elif self.module == "finance":
            return is_config_enabled(self.config.finance)
        elif self.module == "baby":
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

    def gdrive_upload(self):
        Cloud(self.job).upload()

    def check_shows(self):
        ShowDownloader(self.job).check_shows()

    def find_movie(self):
        MovieFinder(self.job).find_movie()

    def organize_media(self):
        RefactorFolder(self.job).update_db()

    def download_torrent(self):
        Transmission(self.job).add_torrent()

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
        cctv.clean_up()
        queues.message_q.put(Message("CCTV Check Completed", job=self.job))

    def get_cctv(self):
        cctv = CCTVChecker(self.job)
        cctv.download_cctv()
        cctv.get_last(10)
        cctv.clean_up()

    def clear_gmail_sent(self):
        cctv = CCTVChecker(self.job)
        cctv.clean_up()

    def add_me_to_cctv(self):
        Subscriptions(self.job).manage_chat_group("cctv")

    def remove_me_from_cctv(self):
        Subscriptions(self.job).manage_chat_group("cctv", remove=True)

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
        Subscriptions(self.job).manage_chat_group("baby")

    def remove_me_from_baby(self):
        Subscriptions(self.job).manage_chat_group("baby", remove=True)

    def git_update(self):
        GitHub(self.job).pull_repo()

    def start_over(self):
        Admin(self.job).start_over()

    def exit_all(self):
        Admin(self.job).exit_all()
        self.send_to_everyone()

    def reboot_pi(self):
        Admin(self.job).reboot_pi()
