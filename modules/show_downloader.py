import feedparser

import refs
from brains.job import Job
from communication.message import Message
from modules.base_module import Module
from modules.transmission import Transmission
from database_manager.sql_connector import sql_databases
from tools.logger import log


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
        log(self._job.job_id, "Show Downloader Object Created")

    def check_shows(self):
        log(self._job.job_id, "-------STARTED TV SHOW CHECK SCRIPT-------")
        feed = feedparser.parse(refs.feed_link)
        show_list = []

        for x in feed.entries:
            episode_name, episode_quality = quality_extract(x.title)

            query = f'SELECT COUNT(1) ' \
                    f'FROM tv_show ' \
                    f'WHERE episode_name="{episode_name}" AND name="{x.tv_show_name}";'

            show_exists = sql_databases["entertainment"].run_sql(query=query)

            if show_exists[0] == 0:
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
            torrent = Transmission(self._job)

            for row in show_list:
                success, torrent_id = torrent.add_torrent(row[2])

                if success:
                    columns = "name, episode_id, episode_name, magnet, quality, torrent_name"
                    val = (row[4], row[0], row[1], row[2], str(row[3]), str(torrent_id))
                    sql_databases["entertainment"].insert('tv_show', columns, val)
                    log(self._job.job_id, torrent_id)

                    message = f'{str(row[1])} added at {str(row[3])} torrent id = {str(torrent_id)}'
                    self.send_message(Message(message, job=self._job, group=refs.group_tv_show))
                else:
                    log(self._job.job_id, "Torrent Add Failed: " + str(row[2]), log_type="error")

        self.send_admin(Message("TV Show Check Completed"))
        log(self._job.job_id, "-------ENDED TV SHOW CHECK SCRIPT-------")
