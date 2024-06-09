import re
import urllib.request

from themoviedb import TMDb

import passwords
from shared_tools.logger import log


def get_movie_info(job_id: int, movie: str) -> (list, list):
    tmdb = TMDb(key=passwords.tmdb_api)

    movies = tmdb.search().movies(query=movie)

    if len(movies) == 0:
        d = re.search(r'\d{4}', movie)
        if d is None:
            return [], []
        movies = tmdb.search().movies(query=movie[0:d.start()].strip())

    movie_titles = []
    movie_posters = []

    for movie in movies:
        if movie.poster_path is None or movie.title is None or movie.year is None:
            continue
        title = f"{movie.title} ({movie.year})".replace("/", "")
        log(job_id=job_id, msg=f"Found Movie: {title}")
        poster_path = f"resources/movie_poster/{title}.jpg".replace(":", "")
        urllib.request.urlretrieve(url="https://image.tmdb.org/t/p/w185"+movie.poster_path,
                                   filename=poster_path)

        movie_titles.append(title)
        movie_posters.append(poster_path)

    return movie_titles, movie_posters
