import feedparser

from shared_models import configuration
from shared_models.job import Job
from shared_models.message import Message
from shared_tools.job_tools import duplicate_and_transform_job
from shared_tools.sql_connector import SQLConnector
from job_handler.base_module import Module
from job_handler.modules.transmission import Transmission
from shared_tools.logger import log


def quality_extract(topic):
    if " 720p" in topic:
        episode_name = topic[0:topic.index(" 720p")].lower()
        episode_quality = 720
    elif " 1080p" in topic:
        episode_name = topic[0:topic.index(" 1080p")].lower()
        episode_quality = 1080
    else:
        episode_name = topic.lower()
        episode_quality = 480
    return episode_name, episode_quality


class ShowDownloader(Module):
    telepot_chat_group = "show"

    def __init__(self, job: Job):
        super().__init__(job)

        self.config = configuration.Configuration().media

        self.db = SQLConnector(job.job_id, database=self.config["database"])
        log(self.job.job_id, "Show Downloader Object Created")

    def check_shows(self):
        log(self.job.job_id, "-------STARTED TV SHOW CHECK SCRIPT-------")
        feed = feedparser.parse(self.config["show_feed"])
        show_list = []

        for x in feed.entries:
            episode_name, episode_quality = quality_extract(x.title)
            show_exists = self.db.check_exists(self.config["tbl_tv_shows"], {'episode_name': episode_name,
                                                                             'name': x.tv_show_name})

            if show_exists == 0:
                found = False
                if len(show_list) != 0:
                    for row in show_list:
                        if row[1] == episode_name:
                            found = True
                            if row[3] > episode_quality:
                                row[0] = x.tv_episode_id
                                row[1] = episode_name
                                row[2] = x.link
                                row[3] = episode_quality
                if not found:
                    show_list.append([x.tv_episode_id, episode_name, x.link, episode_quality, x.tv_show_name])

        if len(show_list) > 0:
            for row in show_list:
                success, torrent_id = Transmission(duplicate_and_transform_job(self.job,
                                                                               "download_torrent",
                                                                               row[2])).add_torrent()

                if success:
                    columns = "name, episode_id, episode_name, magnet, quality, torrent_name"
                    val = (row[4], row[0], row[1], row[2], str(row[3]), str(torrent_id))
                    self.db.insert(self.config["tbl_tv_shows"], columns, val)
                    log(self.job.job_id, torrent_id)
                    self.job.is_background_task = False

                    message = f'{str(row[1])} added at {str(row[3])} torrent id = {str(torrent_id)}'
                    self.send_message(Message(message, job=self.job, group=self.config["telegram_group"]))
                else:
                    log(self.job.job_id, "Torrent Add Failed: " + str(row[2]), log_type="error")

        self.send_admin(Message("TV Show Check Completed"))
        log(self.job.job_id, "-------ENDED TV SHOW CHECK SCRIPT-------")
