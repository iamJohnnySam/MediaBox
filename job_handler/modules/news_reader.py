import feedparser

from shared_models import configuration
from shared_models.message import Message
from shared_tools.job_tools import duplicate_and_transform_job
from shared_tools.sql_connector import SQLConnector
from job_handler.base_module import Module
from shared_models.job import Job
from shared_tools.json_editor import JSONEditor
from shared_tools.logger import log


class NewsReader(Module):
    def __init__(self, job: Job):
        super().__init__(job)

        c = configuration.Configuration()
        self.news_config = c.news

        self.news_db = SQLConnector(job.job_id, database=self.news_config["database"])
        log(self.job.job_id, f"Object Created")

    def _get_news_subscriptions(self):
        result = self.news_db.select(table=self.news_config["tbl_subscriptions"],
                                     columns="subscription",
                                     where={"chat_id": self.job.chat_id},
                                     fetch_all=True)
        subs = [source[0] for source in result]
        log(self.job.job_id, str(subs))
        return subs

    def get_news_all(self):
        self.job.collect("all", 0)
        sources = self._get_news_subscriptions()
        for source in sources:
            self._check_news(source)

    def get_news(self):
        success, source = self.check_value(index=-1, option_list=self._get_news_subscriptions())
        if not success:
            return
        self._check_news(source)

    def _check_news(self, source):
        news_sources = JSONEditor(self.news_config["sources"]).read()
        if source == '':
            log(self.job.job_id, error_code=50005)
            self.job.collection = []
            return
        news_sent = self.news_extractor(source, news_sources[source])
        if not news_sent:
            self.send_message(Message(job=self.job, send_string=f"No new news articles for {source}."))
        self.job.collection = []

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
                log(article, log_type="debug")

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
            val = (source, title, link, self.job.chat_id)

            if self.news_db.check_exists(self.news_config["tbl_news"], {"title": title,
                                                                        "source": source,
                                                                        "user_id": self.job.chat_id}) == 0:
                self.news_db.insert(self.news_config["tbl_news"], cols, val)
                self.send_message(Message(send_string=f'{title} - {link}', job=self.job))
                news_sent = True

        return news_sent

    def subscribe(self):
        sources = JSONEditor(self.news_config["sources"]).read()
        success, source = self.check_value(index=-1,
                                           option_list=[s for s in sources.keys() if type(sources[s]) is not bool],
                                           no_recover=True)
        if not success:
            self.show_news_channels()
            return

        if not self.news_db.check_exists(table=self.news_config["tbl_subscriptions"],
                                         where=f"subscription = '{source}' AND chat_id = '{self.job.chat_id}'") == 0:
            self.news_db.delete(table=self.news_config["tbl_subscriptions"],
                                where=f"chat_id = '{self.job.chat_id}' AND subscription = '{source}';")
            reply_text = f"You are Unsubscribed from {source}."

        else:
            self.news_db.insert(table=self.news_config["tbl_subscriptions"],
                                columns="chat_id, subscription",
                                val=(self.job.chat_id, source))
            reply_text = f"You are now Subscribed to {source}."

        self.send_message(Message(reply_text, job=self.job))

    def show_news_channels(self):
        news = JSONEditor(self.news_config["sources"]).read()
        news_channels = []
        prev_channel = ""
        for channel in news.keys():
            if type(news[channel]) is bool:
                if len(news_channels) != 0:
                    send_message = Message(prev_channel, job=duplicate_and_transform_job(self.job))
                    send_message.keyboard_extractor(function="subscribe_news", options=news_channels,
                                                    reply_to=self.job.reply_to)
                    self.send_message(send_message)
                prev_channel = channel
                news_channels = []
            else:
                news_channels.append(channel)
