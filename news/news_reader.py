from datetime import datetime

import feedparser
import global_var
import logger
from communication import communicator
from database_manager.sql_connector import db_news


class NewsReader:
    telepot_account = "news"
    telepot_chat_group = "news"

    def __init__(self):
        self.id_prefix = "http://www.adaderana.lk/news.php?nid="
        logger.log("Object Created")

    def run_code(self):
        logger.log("-------STARTED NEWS READER SCRIPT-------")
        self.adaderana_news()
        self.dailymirror_cartoon()
        logger.log("-------ENDED NEWS READER SCRIPT-------")

    def adaderana_news(self):
        database_table = "adaderana_news"
        last_news_id = db_news.get_last_id(database_table, "news_id")

        feed = feedparser.parse(global_var.news_adaderana)

        for article in feed.entries:
            article_id = int(article.id.replace(self.id_prefix, ""))
            if article_id > last_news_id:
                if db_news.exists(database_table, f"news_id = '{article_id}'") == 0:
                    cols = "news_id, title, pub_date, link"
                    val = (article_id, article.title, article.published, article.link)
                    db_news.insert(database_table, cols, val)

                    communicator.send_to_group(self.telepot_account,
                                               article.title + " - " + article.link,
                                               self.telepot_chat_group)
                    logger.log(article_id)

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
            if db_news.exists(database_table, f"date = '{article_date}'") == 0:
                db_news.insert(database_table, cols, val)

                communicator.send_to_group(self.telepot_account,
                                           image,
                                           self.telepot_chat_group)
                logger.log(article.title)
