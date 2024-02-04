import feedparser

import logger


def get_movies_by_name(movie: str):
    retries = 2

    movie = movie.lower()
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
        if retries == 0:
            break
        logger.log("Retrying searching " + search_string, message_type="warn")
        movie_feed = feedparser.parse(search_string)
        retries = retries - 1

    movies = []
    for movie in movie_feed:
        if first_word in movie.title:
            movies.append(movie)

    if len(movies) == 0:
        movies = movie_feed

    return movies


def get_movie_details(movie):
    image_string = movie.summary_detail.value
    sub1 = 'src="'
    idx1 = image_string.index(sub1)
    idx2 = image_string.index('" /></a>')
    image = image_string[idx1 + len(sub1): idx2]
    return movie.title, image, movie.link, movie.links[1].href
