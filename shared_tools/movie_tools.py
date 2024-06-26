import re
import urllib.request

from themoviedb import TMDb

import passwords
from shared_tools.logger import log


def get_movie_info(job_id: int, s_movie: str = None) -> (list, list):
    tmdb = TMDb(key=passwords.tmdb_api)

    movies = tmdb.search().movies(query=s_movie)

    movie_titles = []
    movie_posters = []

    for movie in movies:
        if movie.poster_path is None or movie.title is None or movie.year is None:
            continue
        title = f"{movie.title} ({movie.year})".replace("/", "")
        log(job_id=job_id, msg=f"Found Movie: {title}")
        poster_path = f"resources/movie_poster/{title}.jpg".replace(":", "")
        urllib.request.urlretrieve(url="https://image.tmdb.org/t/p/w185" + movie.poster_path,
                                   filename=poster_path)

        movie_titles.append(title)
        movie_posters.append(poster_path)

    d = re.search(r'\d{4}', s_movie)
    if d is not None:
        movies2 = tmdb.search().movies(query=s_movie[0:d.start()].strip())
        for movie in movies2:
            if movie.poster_path is None or movie.title is None or movie.year is None:
                continue
            title = f"{movie.title} ({movie.year})".replace("/", "")
            if title in movie_titles:
                continue
            log(job_id=job_id, msg=f"Found Movie: {title}")
            poster_path = f"resources/movie_poster/{title}.jpg".replace(":", "")
            urllib.request.urlretrieve(url="https://image.tmdb.org/t/p/w185" + movie.poster_path,
                                       filename=poster_path)
            movie_titles.append(title)
            movie_posters.append(poster_path)

    return movie_titles, movie_posters


def get_show_info(job_id: int, show: str = None) -> (list, list):
    tmdb = TMDb(key=passwords.tmdb_api)

    d = re.search(r'\d{4}', show)
    if d is None:
        movies = tmdb.search().tv(query=show)
    else:
        movies = tmdb.search().tv(query=show[0:d.start()].strip())

    movie_titles = []
    movie_posters = []

    for movie in movies:
        if movie.poster_path is None or movie.name is None or movie.year is None:
            continue
        title = f"{movie.name} ({movie.year})".replace("/", "")
        log(job_id=job_id, msg=f"Found Movie: {title}")
        poster_path = f"resources/movie_poster/{title}.jpg".replace(":", "")
        urllib.request.urlretrieve(url="https://image.tmdb.org/t/p/w185" + movie.poster_path,
                                   filename=poster_path)

        movie_titles.append(title)
        movie_posters.append(poster_path)

    return movie_titles, movie_posters
