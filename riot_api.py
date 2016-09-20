import asyncio
import aiohttp
import time

RIOT_API_URL = 'https://na.api.pvp.net'

class RiotApiHttpException(Exception):
    """Raised whenever an HTTP request does not return 200"""
    def __init__(self, response):
        self.response = response

class RiotApiRateExceededException(Exception):
    """Raised whenever the api rate limit has been passed"""
    def __init__(self, response):
        self.response = response

class RiotApi(object):
    def __init__(self, loop, api_key):
        self.session = aiohttp.ClientSession(loop=loop)
        self.key = api_key
        self.timeout = 10

        # technically 10 req / 10 sec, but
        # that still triggers a 429. This doesn't.
        self.limit_messages = 8.0
        self.limit_time = 10.0
        self.last_time = time.time()
        self.bucket = self.limit_messages

    @asyncio.coroutine
    def request_url_json(self, url, params, limit=True):
        # simple token bucket limiting
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        self.bucket += delta_time * (self.limit_messages / self.limit_time)
        if self.bucket > self.limit_messages:
            self.bucket = self.limit_messages
        if self.bucket < 1:
            raise RiotApiRateExceededException("Riot Api rate request exceeded. Please wait until making the next request")
        self.bucket -= 1
        with aiohttp.Timeout(self.timeout):
            response = yield from self.session.get(url, params=params)
            if response.status != 200:
                raise RiotApiHttpException(response.status)
            return (yield from response.json())

    @asyncio.coroutine
    def get_champion(self, region='na', **kwargs):
        api_path = '/api/lol/{}/v1.2/champion'
        api_path = api_path.format(region)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_champion_by_id(self, championID, region='na', **kwargs):
        api_path = '/api/lol/{}/v1.2/champion/{}'
        api_path = api_path.format(region, championID)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_league_by_summonerid(self, summonerID, region='na', **kwargs):
        api_path = '/api/lol/{}/v2.5/league/by-summoner/{}'
        api_path = api_path.format(region, summonerID)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_match_by_tournament(self, tournament_code, region='na', **kwargs):
        api_path = '/api/lol/{}/v2.2/match/by-tournament/{}/ids'
        api_path = api_path.format(region, tournament_code)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_match_for_tournament(self, matchID, region='na', **kwargs):
        api_path = '/api/lol/{}/v2.2/match/for-tournament/{}'
        api_path = api_path.format(region, matchID)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_live_match(self, summonerID, platformID='NA1', **kwargs):
        api_path = '/observer-mode/rest/consumer/getSpectatorGameInfo/{}/{}'
        api_path = api_path.format(platformID, summonerID)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_match(self, matchID, region='na', **kwargs):
        api_path = '/api/lol/{}/v2.2/match/{}'
        api_path = api_path.format(region, matchID)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_matchlist(self, summonerID, region='na', **kwargs):
        api_path = '/api/lol/{}/v2.2/matchlist/by-summoner/{}'
        api_path = api_path.format(region, summonerID)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_stats_ranked(self, summonerID, region='na', **kwargs):
        api_path = '/api/lol/{}/v1.3/stats/by-summoner/{}/ranked'
        api_path = api_path.format(region, summonerID)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_stats_summary(self, summonerID, region='na', **kwargs):
        api_path = '/api/lol/{}/v1.3/stats/by-summoner/{}/summary'
        api_path = api_path.format(region, summonerID)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_summoner_by_name(self, summoner_names, region='na', **kwargs):
        api_path = '/api/lol/{}/v1.4/summoner/by-name/{}'
        api_path = api_path.format(region, ','.join(summoner_names))
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_summoner_by_id(self, summoner_ids, region='na', **kwargs):
        api_path = '/api/lol/{}/v1.4/summoner/{}'
        api_path = api_path.format(region, ','.join(summoner_ids))
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_static_champion(self, region='na', **kwargs):
        api_path = '/api/lol/static-data/{}/v1.2/champion'
        api_path = api_path.format(region)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_static_summoner_spell(self, region='na', **kwargs):
        #https://global.api.pvp.net/api/lol/static-data/na/v1.2/summoner-spell?dataById=true&spellData=all
        api_path = '/api/lol/static-data/{}/v1.2/summoner-spell'
        api_path = api_path.format(region)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_static_champion_by_id(self, championID, region='na', **kwargs):
        api_path = '/api/lol/static-data/{}/v1.2/champion/{}'
        api_path = api_path.format(region, championID)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))

    @asyncio.coroutine
    def get_recent_matches_by_id(self, summonerID, region='na', **kwargs):
        api_path = '/api/lol/{}/v1.3/game/by-summoner/{}/recent'
        api_path = api_path.format(region,summonerID)
        api_url = RIOT_API_URL + api_path
        params = {'api_key':self.key}
        params.update(kwargs)
        return (yield from self.request_url_json(api_url, params))
