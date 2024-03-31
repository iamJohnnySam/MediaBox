import feedparser

import refs
from communication.message import Message
from modules.base_module import Module
from modules.subscriptions import Subscriptions
from tools import logger
from brains.job import Job
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import sql_databases


class NewsReader(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        logger.log(self._job.job_id, f"Object Created")
        self.admin_db = sql_databases[refs.db_admin]
        self.news_db = sql_databases[refs.db_news]

    def _get_news_subscriptions(self):
        query = f"SELECT group_name FROM {refs.tbl_groups} WHERE chat_id = {self._job.chat_id}"
        result = self.admin_db.run_sql(query, job_id=self._job.job_id, fetch_all=True)
        subs = [source[0].replace("news_", "") for source in result if source[0].startswith("news_")]
        logger.log(self._job.job_id, str(subs))
        return subs

    def get_news_all(self):
        self._job.collect("all", 0)
        sources = self._get_news_subscriptions()
        for source in sources:
            self._check_news(source)
        self._job.complete()

    def get_news(self):
        success, source = self.check_value(index=-1, option_list=self._get_news_subscriptions())
        if not success:
            return
        self._check_news(source)
        self._job.complete()

    def _check_news(self, source):
        news_sources = JSONEditor(refs.news_sources).read()
        news_sent = self.news_extractor(source, news_sources[source])
        if not news_sent:
            self.send_message(Message(job=self._job, send_string=f"No new news articles for {source}."))
        self._job.collection = []

    def news_extractor(self, source: str, news):
        news_sent = False

        if type(news) is dict:
            article_source = news["source"]
            article_title = news["title"]
            article_link = news["link"]

            debug = "debug" in news.keys() and news["debug"]
            photo_link = "photo_link" in news.keys() and news["photo_link"]

            if "pause" in news.keys() and news["pause"]:
                return
        else:
            article_source = news
            article_title = "title"
            article_link = "link"
            debug = False
            photo_link = False

        feed = feedparser.parse(article_source)

        for article in feed.entries:
            if debug:
                logger.log(article, log_type="debug")

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

            cols = "source, title, link, user_id"
            val = (source, title, link, self._job.chat_id)

            if self.news_db.exists(refs.tbl_news, f"title = '{title}' AND source = '{source}'"
                                                  f" AND user_id = '{self._job.chat_id}'") == 0:
                self.news_db.insert(refs.tbl_news, cols, val)
                self.send_message(Message(send_string=f'{title} - {link}', job=self._job))
                news_sent = True

        return news_sent

    def show_news_channels(self):
        news = JSONEditor(refs.news_sources).read()
        news_channels = []
        prev_channel = ""
        for channel in news.keys():
            if type(news[channel]) is bool:
                if len(news_channels) != 0:
                    send_message = Message(prev_channel, job=self._job)
                    send_message.one_time_keyboard_extractor("subs_news", news_channels)

                prev_channel = channel
                news_channels = []
            else:
                news_channels.append(channel)

    def subscribe(self):
        sources = JSONEditor(refs.news_sources).read()
        success, source = self.check_value(index=-1,
                                           option_list=[s for s in sources.keys() if type(sources[s]) is not bool],
                                           no_recover=True)
        if not success:
            self.show_news_channels()

        if not self.admin_db.exists(refs.tbl_groups,
                                    f"group_name = 'news_{source}' AND chat_id = '{self._job.chat_id}'") == 0:
            Subscriptions(self._job).manage_chat_group(f'news_{source}', add=False, remove=True)
            reply_text = f"You are Unsubscribed from {source}."

        else:
            Subscriptions(self._job).manage_chat_group(f'news_{source}')
            reply_text = f"You are now Subscribed to {source}."

        self.send_message(Message(reply_text, job=self._job))
