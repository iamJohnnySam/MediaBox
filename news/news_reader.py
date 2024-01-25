from datetime import datetime

import feedparser
import global_var
import logger
from communication import communicator
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import sql_databases


class NewsReader:

    def __init__(self):
        self.database_table = "news_articles"
        self.telepot_account = "news"
        logger.log("Object Created")

    def run_code(self):
        logger.log("------- STARTED NEWS READER SCRIPT -------")

        news_sources = JSONEditor(global_var.news_sources).read()
        for source in news_sources.keys():
            if "pause" in news_sources[source].keys() and news_sources[source]["pause"]:
                continue
            self.news_extractor(source, news_sources[source])

        logger.log("------- ENDED NEWS READER SCRIPT -------")

    def news_extractor(self, source: str, news):
        if type(news) is dict:
            article_source = news["source"]
            article_title = news["title"]
            article_link = news["link"]

            debug = "debug" in news.keys() and news["debug"]
            photo_link = "photo_link" in news.keys() and news["photo_link"]

        else:
            article_source = news
            article_title = "title"
            article_link = "link"
            debug = False
            photo_link = False

        feed = feedparser.parse(article_source)

        for article in feed.entries:

            if debug:
                logger.log(article, message_type="debug")

            # title
            title = getattr(article, article_title)
            if "'" in str(title):
                title = title.replace("'", "\"")
            if '"' in title:
                title = title.replace('"', '\"')

            # link
            link = getattr(article, article_link)
            if photo_link:
                if "link_prefix" in news.keys():
                    idx1 = link.index(news["link_prefix"])
                    len_idx1 = len(news["link_prefix"])
                else:
                    idx1 = 0
                    len_idx1 = 0
                if "link_suffix" in news.keys():
                    idx2 = link.index(news["link_suffix"])
                else:
                    idx2 = len(link)
                link = link[idx1 + len_idx1: idx2]

            cols = "source, title, link"
            val = (source, title, link)
            if sql_databases["news"].exists(self.database_table, f"title = '{title}' AND source = '{source}'") == 0:
                sql_databases["news"].insert(self.database_table, cols, val)

                communicator.send_to_group(self.telepot_account, f'{title} - {link}', f'news_{source}')
                logger.log(f'{source} > {title}')
