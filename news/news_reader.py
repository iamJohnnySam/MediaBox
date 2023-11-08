import feedparser
import settings
from communication import communicator
from datetime import datetime
from database_manager.json_editor import JSONEditor


class NewsReader:
    def __init__(self):
        self.id_inhibitor = "http://www.adaderana.lk/news.php?nid="
        self.news_database = JSONEditor(settings.news_database)
        self.data = self.news_database.read()
        self.last_clean = datetime(2022, 11, 2, 14, 40, 00, 000000)

    def run_code(self):
        feed = feedparser.parse(settings.news_link)
        self.data = self.news_database.read()

        available_news = []

        for x in feed.entries:
            news_id = x.id
            news_id = news_id.replace(self.id_inhibitor, "")
            available_news.append(news_id)

            if news_id not in self.data:
                print(news_id)
                new_news = {
                    news_id: [{
                        "Title": x.title,
                        "Pub Date": x.published,
                        "Link": x.link,
                    }]
                }
                self.news_database.add_level1(new_news)

                communicator.send_now(x.title + " - " + x.link, "news", cctv=False)

        if (datetime.now() - self.last_clean).days >= 1:
            print("Starting News Clean-up")
            self.news_database.delete(available_news)
            print("Cleaned News Database")
            self.last_clean = datetime.now()

        print("------- NEWS -------")
