import os
import requests
from abc import ABC, abstractmethod

from mr_knowledge_bot.bot.clients.base_client import BaseClient
from mr_knowledge_bot.bot.entites.the_movie_db.genre_entity import Genre


def poll_by_page_and_limit(limit=500):
    """
    Args:
        limit (int): the maximum number of records to query from the api.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            objects, page = [], 1
            kwargs['page'] = page

            while current_objects_by_page := func(self, *args, **kwargs):
                objects.extend(current_objects_by_page)
                if len(objects) > limit:
                    break
                page += 1
                kwargs['page'] = page
            return objects[:limit]

        return wrapper
    return decorator


class TheMovieDBBaseClient(BaseClient, ABC):
    BASE_URL = os.getenv('MOVIE_BASE_URL')
    genre_entity = Genre

    def __init__(self, token=None, base_url=None, verify=True):
        super().__init__(
            token=token or os.getenv('API_MOVIE_TOKEN'), base_url=base_url or self.BASE_URL, verify=verify
        )

    def get(self, url, params=None):
        if not params:
            params = {}
        params.update({'api_key': self.token})
        return requests.request('GET', f'{self.base_url}{url}', params=params, verify=self.verify)

    @abstractmethod
    def search(self, **kwargs):
        pass

    @abstractmethod
    def get_genres(self):
        pass

    @abstractmethod
    def discover(self, **kwargs):
        pass
