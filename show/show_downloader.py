import feedparser
import os
import time
import global_var
import logger
from communication import communicator
from database_manager.json_editor import JSONEditor
from show import transmission


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


class ShowDownloader:
    telepot_chat_group = "show"
    telepot_account = "main"

    def __init__(self):
        self.shows = JSONEditor(global_var.show_download_database)
        self.data = self.shows.read()
        logger.log("Show Downloader Object Created")

    def run_code(self):
        logger.log("-------STARTED TV SHOW CHECK SCRIPT-------")
        feed = feedparser.parse(global_var.feed_link)
        self.data = self.shows.read()
        show_list = []

        for x in feed.entries:
            if x.tv_show_name not in self.data:
                new_show = {
                    x.tv_show_name: [{"episode_id": 0, "episode_name": "test", "magnet": "test", "quality": "480"}]}
                self.shows.add_level1(new_show)
                self.data = self.shows.read()

            episode_name, episode_quality = quality_extract(x.title)

            if any(player['episode_name'] == episode_name for player in self.data[x.tv_show_name]):
                pass
            else:
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

        for row in show_list:
            show = {"episode_id": row[0], "episode_name": row[1], "magnet": row[2], "quality": str(row[3])}
            success, torrent_id = transmission.download(row[2])
            # torrent_id = os.system("transmission-remote -a " + row[2])

            if success:
                self.shows.add_level2(row[4], show)
                self.data = self.shows.read()
                logger.log(torrent_id, source="TOR")

                message = str(row[1]) + " added at " + str(row[3]) + " torrent id = " + str(torrent_id)
                communicator.send_to_group(self.telepot_account,
                                           message,
                                           group=self.telepot_chat_group)
                logger.log(message, source="SHOW")
                time.sleep(3)

            else:
                logger.log("Torrent Add Failed: " + str(row[2]), source="TOR", message_type="error")

        communicator.send_to_master(self.telepot_account, "TV Show Check Completed")
        logger.log("-------ENDED TV SHOW CHECK SCRIPT-------")
