import feedparser
import global_var
import logger
from communication import communicator
from datetime import datetime
from database_manager.json_editor import JSONEditor


class NewsReader:
    telepot_account = "news"
    telepot_chat_group = "news"

    def __init__(self):
        self.id_inhibitor = "http://www.adaderana.lk/news.php?nid="
        self.news_database = JSONEditor(global_var.news_database)
        self.data = self.news_database.read()
        self.last_clean = datetime(2022, 11, 2, 14, 40, 00, 000000)
        logger.log("News Watcher Object Created")

    def run_code(self):
        logger.log("-------STARTED NEWS READER SCRIPT-------")
        feed = feedparser.parse(global_var.news_link)
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
                logger.log(news_id, source="NEWS")

        if (datetime.now() - self.last_clean).days >= 1:
            self.news_database.delete(available_news)
            self.last_clean = datetime.now()

        logger.log("-------ENDED NEWS READER SCRIPT-------")
