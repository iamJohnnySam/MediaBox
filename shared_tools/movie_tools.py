import re

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

    print(movies)
    print(len(movies))
    for movie in movies:
        print(movie)
        movie_id = movie.id
        movie = tmdb.movie(movie_id).details(append_to_response="credits,external_ids,images,videos")
        print(movie.title, movie.year)
        print(movie.tagline)
        print(movie.poster_url)
        print(movie.external_ids.imdb_url)

    return movies
