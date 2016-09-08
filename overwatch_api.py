import asyncio
import aiohttp
import time

OVERWATCH_API_URL = 'https://api.lootbox.eu'

class OverwatchApiHttpException(Exception):
    """Raised whenever an HTTP request does not return 200"""
    def __init__(self, response):
        self.response = response

class OverwatchApiRateExceededException(Exception):
    """Raised whenever the api rate limit has been passed"""

class OverwatchApi(object):
    def __init__(self, loop):
        self.session = aiohttp.ClientSession(loop=loop)
        self.timeout = 20

        # technically 10 req / 10 sec, but
        # that still triggers a 429. This doesn't.
        self.limit_messages = 8.0
        self.limit_time = 10.0
        self.last_time = time.time()
        self.bucket = self.limit_messages

    @asyncio.coroutine
    def request_url_json(self, url, limit=True):
        # simple token bucket limiting
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        self.bucket += delta_time * (self.limit_messages / self.limit_time)
        if self.bucket > self.limit_messages:
            self.bucket = self.limit_messages
        if self.bucket < 1:
            raise OverwatchApiRateExceededException()
        self.bucket -= 1
        with aiohttp.Timeout(self.timeout):
            response = yield from self.session.get(url)
            if response.status != 200:
                raise OverwatchApiHttpException(response.status)
            return (yield from response.json())

    @asyncio.coroutine
    def get_player_profile(self, player):
        api_path = '/pc/us/{}/profile'
        api_path = api_path.format(player)
        api_url = OVERWATCH_API_URL + api_path
        return (yield from self.request_url_json(api_url))

    @asyncio.coroutine
    def get_player_hero_info(self, player):
        api_path = '/pc/us/{}/quick-play/heroes'
        api_path = api_path.format(player)
        api_url = OVERWATCH_API_URL + api_path
        return (yield from self.request_url_json(api_url))

    @asyncio.coroutine
    def get_specific_hero_info(self, player, hero):
        api_path = '/pc/us/{}/competitive-play/hero/{}/'
        api_path = api_path.format(player, hero)
        api_url = OVERWATCH_API_URL + api_path
        return (yield from self.request_url_json(api_url))