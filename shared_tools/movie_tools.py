import re
import urllib.request

from themoviedb import TMDb

import passwords


def get_movie_info(movie: str):
    tmdb = TMDb(key=passwords.tmdb_api)

    movies = tmdb.search().movies(query=movie)

    if len(movies) == 0:
        d = re.search(r'\d{4}', movie)
        if d is None:
            return
        movies = tmdb.search().movies(query=movie[0:d.start()].strip())

    if len(movies) == 0:
        return

    for movie in movies:
        urllib.request.urlretrieve(movie.poster_path, f"{movie.title} ({movie.year}).jpg")

    return movies
