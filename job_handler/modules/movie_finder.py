import feedparser

from shared_models.message import Message
from job_handler.base_module import Module
from shared_models.job import Job
from shared_tools.job_tools import transform_and_queue_job
from shared_tools.logger import log


class MovieFinder(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        self.retries = 2
        log(self.job.job_id, f"Movie Finder Module Created")

    def find_movie(self):
        if self.job.called_back and self.check_index() > 1:
            movie = self.get_index(1)
            transform_and_queue_job(self.job, "download_torrent", movie)
            return

        success, movie = self.check_value(index=-1, description="name of the movie")
        if not success:
            return

        movie = movie.lower()

        search_filter: list = movie.split(" ")
        for word in ["the", "a", "in", "an"]:
            while word in search_filter:
                search_filter.remove(word)
        log(job_id=self.job.job_id, msg=f"Search filter words selected as {str(search_filter)}.")

        movie = movie.replace(" ", "%20").replace("/", "")
        search_string = "https://yts.mx/rss/" + movie + "/720p/all/0/en"
        log(self.job.job_id, msg="Searching " + search_string)
        movie_feed = feedparser.parse(search_string)

        while not movie_feed:
            if self.retries == 0:
                break
            log(self.job.job_id, "Retrying searching " + search_string, log_type="warn")
            movie_feed = feedparser.parse(search_string)
            self.retries = self.retries - 1

        movies = []
        for movie in movie_feed.entries:
            log(job_id=self.job.job_id, msg=f"Found movie - {movie.title}")
            if all(word in str(movie.title).lower() for word in search_filter):
                movies.append(movie)
                log(job_id=self.job.job_id, msg=f"Movie matching search criteria - {movie.title}")

        if len(movies) == 0:
            movies = movie_feed.entries

        options = []
        btn_text = []
        for movie_entry in movies:
            title, image, link, torrent = get_movie_details(movie_entry)
            send_movie = Message(f"{title}\n{image}", job=self.job)
            self.send_message(send_movie)
            options.append(torrent)
            title: str = title.replace("[", "").replace("]", "").replace("YTS.MX", "").strip()
            btn_text.append(title)

        number_list = []
        i = 1
        send_string = f"Search for {search_string} resulted in following.\nWhich movie do you want to download?"
        for btn_val in btn_text:
            send_string = send_string + f"\n{i:>02}: {btn_val}"
            number_list.append(i)
            i = i+1
        download_movie = Message(send_string, job=self.job)
        download_movie.keyboard_extractor(function=self.job.function,
                                          options=options,
                                          index=1,
                                          button_text=number_list,
                                          bpr=5,
                                          add_cancel=True,
                                          reply_to=self.job.reply_to,
                                          collection=self.job.collection)
        self.send_message(download_movie)


def get_movie_details(movie) -> (str, str, str, str):
    image_string = movie.summary_detail.value
    sub1 = 'src="'
    idx1 = image_string.index(sub1)
    idx2 = image_string.index('" /></a>')
    image = image_string[idx1 + len(sub1): idx2]
    return movie.title, image, movie.link, movie.links[1].href
