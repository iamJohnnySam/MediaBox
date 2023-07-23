import feedparser
import os
import json
import time
import settings


class ShowDownloader:
    def __init__(self):
        with open(settings.show_download_database, 'r') as file:
            self.data = json.load(file)

    def update_json(self, new_data, series):
        with open(settings.show_download_database, 'r+') as file:
            file_data = json.load(file)
            file_data[series].append(new_data)
            file.seek(0)
            json.dump(file_data, file, indent=4)
        with open(settings.show_download_database, 'r') as file:
            self.data = json.load(file)

    def update_json2(self, new_data):
        with open(settings.show_download_database, 'r+') as file:
            file_data = json.load(file)
            file_data.update(new_data)
            file.seek(0)
            json.dump(file_data, file, indent=4)
        with open(settings.show_download_database, 'r') as file:
            self.data = json.load(file)

    def run_code(self):
        feed = feedparser.parse(settings.feed_link)

        with open(settings.show_download_database, 'r') as file:
            self.data = json.load(file)

        show_list = []

        for x in feed.entries:
            if x.tv_show_name in self.data:
                pass
            else:
                new_show = {
                    x.tv_show_name: [{"episode_id": 0, "episode_name": "test", "magnet": "test", "quality": "480"}]}
                self.update_json2(new_show)

            tmp = x.title[-4:]

            if tmp == "720p":
                episode_name = x.title[:-5].lower()
                episode_quality = 720
            elif tmp == "080p":
                episode_name = x.title[:-6].lower()
                episode_quality = 1080
            else:
                episode_name = x.title.lower()
                episode_quality = 480

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
            self.update_json(show, row[4])

            os.system("transmission-gtk " + row[2])

            settings.bot.sendMessage(settings.telepot_chat, str(row[1]) + " added at " + str(row[3]))
            time.sleep(3)

        settings.bot.sendMessage(settings.telepot_chat, "TV Show Check Ran Successfully")
