import feedparser
import os
import time
import settings
import communicator
from editor import JSONEditor


class NewsReader:
    def __init__(self):
        self.news_database = JSONEditor(settings.news_database)
        self.data = self.news_database.read()

    def run_code(self):
        feed = feedparser.parse(settings.news_link)
        self.data = self.news_database.read()

        for x in feed.entries:
            news_id = x.id
            news_id = news_id.replace("http://www.adaderana.lk/news.php?nid=", "")

            if news_id not in self.data:
                new_news = {
                    news_id: [{
                        "Title": x.title,
                        "Pub Date": x.published,
                        "Link": x.link,
                    }]
                }
                self.news_database.add_level1(new_news)
                self.data = self.news_database.read()

                communicator.send_now("--- NEWS ---", "news", cctv=False)
                communicator.send_now(x.title + " - " + x.link, "news", cctv=False)

        print("------- NEWS -------")
