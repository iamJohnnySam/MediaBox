from themoviedb import TMDb

import passwords


def get_movie_info(movie: str):
    tmdb = TMDb(key=passwords.tmdb_api)

    movies = tmdb.search().movies(query=movie)
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
