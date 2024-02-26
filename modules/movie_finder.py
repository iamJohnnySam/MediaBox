import feedparser

from record import logger
from communication.channels import channels
from job_handling.job import Job


class MovieFinder:
    def __init__(self, message: Job):
        self.msg = message
        self.retries = 2
        self.channel = channels[self.msg.telepot_account]

    def start(self):
        if not self.msg.check_value():
            self.channel.get_value_from_user(msg=self.msg, inquiry="name of movie")
            return

        movie = self.msg.value.lower()

        first_word = movie.split(" ")[0]
        if first_word in ["the", "a", "in", "an"]:
            try:
                first_word = movie.split(" ")[1]
            except IndexError:
                pass

        movie = movie.replace(" ", "%20").replace("/", "")
        search_string = "https://yts.mx/rss/" + movie + "/720p/all/0/en"
        logger.log("Searching " + search_string)
        movie_feed = feedparser.parse(search_string)

        while not movie_feed:
            if self.retries == 0:
                break
            logger.log("Retrying searching " + search_string, log_type="warn")
            movie_feed = feedparser.parse(search_string)
            self.retries = self.retries - 1

        movies = []
        for movie in movie_feed.entries:
            if first_word in movie.title:
                movies.append(movie)

        if len(movies) == 0:
            movies = movie_feed

        for movie_name in movies:
            title, image, link, torrent = get_movie_details(movie_name)

            self.channel.send_with_keyboard(send_string=title,
                                            job=self.msg,
                                            photo=image,
                                            button_text=["Visit Page", "Download", "Cancel"],
                                            button_val=[f"echo;{link}", f"torrent;{torrent}", "cancel"],
                                            arrangement=[3])


def get_movie_details(movie):
    image_string = movie.summary_detail.value
    sub1 = 'src="'
    idx1 = image_string.index(sub1)
    idx2 = image_string.index('" /></a>')
    image = image_string[idx1 + len(sub1): idx2]
    return movie.title, image, movie.link, movie.links[1].href
