from datetime import datetime

import feedparser
import global_var
import logger
import settings
from communication import communicator
from database_manager.sql_connector import SQLConnector


class NewsReader:
    telepot_account = "news"
    telepot_chat_group = "news"
    source = "NEWS"

    def __init__(self):
        self.id_prefix = "http://www.adaderana.lk/news.php?nid="
        self.database = SQLConnector(settings.database_user, settings.database_password, 'news')
        logger.log("Object Created", source=self.source)

    def run_code(self):
        logger.log("-------STARTED NEWS READER SCRIPT-------", source=self.source)
        self.adaderana_news()
        self.dailymirror_cartoon()
        self.parliament_news()
        logger.log("-------ENDED NEWS READER SCRIPT-------", source=self.source)

    def adaderana_news(self):
        database_table = "adaderana_news"
        last_news_id = self.database.get_last_id(database_table, "news_id")

        feed = feedparser.parse(global_var.news_adaderana)

        for article in feed.entries:
            article_id = int(article.id.replace(self.id_prefix, ""))
            if article_id > last_news_id:
                if self.database.check_exists(database_table, f"news_id = '{article_id}'") == 0:
                    cols = "news_id, title, pub_date, link"
                    val = (article_id, article.title, article.published, article.link)
                    self.database.insert(database_table, cols, val)

                    communicator.send_to_group(self.telepot_account,
                                               article.title + " - " + article.link,
                                               self.telepot_chat_group)
                    logger.log(article_id, source=self.source)

    def dailymirror_cartoon(self):
        database_table = "dailymirror_cartoon"

        feed = feedparser.parse(global_var.news_cartoon)

        for article in feed.entries:
            article_date = datetime.strptime(article.title[-10:], "%d-%m-%Y")

            image_string = article.summary
            sub1 = '<img src="'
            idx1 = image_string.index(sub1)
            idx2 = image_string.index('" /></p>')
            image = image_string[idx1 + len(sub1): idx2]

            cols = "title, link, date"
            val = (article.title, image, article_date)
            if self.database.check_exists(database_table, f"date = '{article_date}'") == 0:
                self.database.insert(database_table, cols, val)

                communicator.send_to_group(self.telepot_account,
                                           image,
                                           self.telepot_chat_group)
                logger.log(article.title, source=self.source)

    def parliament_news(self):
        database_table = "dailymirror_cartoon"

        feed = feedparser.parse(global_var.news_parliament)
        print(feed)
        print()

        for article in feed.entries:
            print(article)
