from tmdb import route

import passwords

base = route.Base()
base.key = passwords.tmdb_api


async def get_movie_info(movie: str):

    movies = await route.Movie().search(movie)
