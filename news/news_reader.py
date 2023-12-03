import feedparser

import logger
import settings
from communication import communicator
from datetime import datetime
from database_manager.json_editor import JSONEditor


class NewsReader:
    telepot_account = "main"
    telepot_chat_group = "news"

    def __init__(self):
        self.id_inhibitor = "http://www.adaderana.lk/news.php?nid="
        self.news_database = JSONEditor(settings.news_database)
        self.data = self.news_database.read()
        self.last_clean = datetime(2022, 11, 2, 14, 40, 00, 000000)
        logger.log("News Watcher Object Created")

    def run_code(self):
        feed = feedparser.parse(settings.news_link)
        self.data = self.news_database.read()

        available_news = []

        for x in feed.entries:
            news_id = x.id
            news_id = news_id.replace(self.id_inhibitor, "")
            available_news.append(news_id)

            if news_id not in self.data:
                new_news = {
                    news_id: [{
                        "Title": x.title,
                        "Pub Date": x.published,
                        "Link": x.link,
                    }]
                }
                self.news_database.add_level1(new_news)

                communicator.send_to_group(self.telepot_account,
                                           x.title + " - " + x.link,
                                           self.telepot_chat_group)
                logger.log(news_id + ": " + x.title, source="NEWS")

        if (datetime.now() - self.last_clean).days >= 1:
            logger.log("Starting News Clean-up")
            self.news_database.delete(available_news)
            logger.log("Cleaned News Database")
            self.last_clean = datetime.now()

        logger.log("------- NEWS -------")
