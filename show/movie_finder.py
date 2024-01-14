import feedparser

import logger


def get_movies_by_name(movie):
    movie = movie.lower().replace(" ", "%20")
    movie = movie.lower().replace("/", "")
    search_string = "https://yts.mx/rss/" + movie + "/720p/all/0/en"

    logger.log("Searching " + search_string, source="MOV")
    movie_feed = feedparser.parse(search_string)
    return movie_feed


def get_movie_details(movie):
    image_string = movie.summary_detail.value
    sub1 = 'src="'
    idx1 = image_string.index(sub1)
    idx2 = image_string.index('" /></a>')
    image = image_string[idx1 + len(sub1): idx2]
    return movie.title, image, movie.link, movie.links[1].href
