import feedparser
import global_var
import logger
import settings
from communication import communicator
from datetime import datetime
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import SQLConnector


class NewsReader:
    telepot_account = "news"
    telepot_chat_group = "news"
    database_table = "adaderana_news"

    def __init__(self):
        self.id_prefix = "http://www.adaderana.lk/news.php?nid="
        self.database = SQLConnector(settings.database_user, settings.database_password, 'news')
        self.last_news_id = self.database.get_last_id(self.database_table, "news_id")
        logger.log("Object Created")

    def run_code(self):
        logger.log("-------STARTED NEWS READER SCRIPT-------")
        feed = feedparser.parse(global_var.news_link)

        for article in feed.entries:
            article_id = int(article.id.replace(self.id_prefix, ""))
            if article_id > self.last_news_id:
                if not self.database.check_exists(self.database_table, f'news_id = "{article_id}"'):
                    cols = "news_id, title, pub_date, link"
                    val = (article_id, article.title, article.published, article.link)
                    self.database.insert(self.database_table, cols, val)

                    communicator.send_to_group(self.telepot_account,
                                               article.title + " - " + article.link,
                                               self.telepot_chat_group)
                    logger.log(article_id, source="NEWS")

        self.last_news_id = self.database.get_last_id(self.database_table, "news_id")

        logger.log("-------ENDED NEWS READER SCRIPT-------")
