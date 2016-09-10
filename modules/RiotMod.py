import asyncio
import riot_api
import datetime

class RiotMod(object):
    def __init__(self, bot):
        self.commands = {
            "rank": self.on_rank,
            "matchlist": self.on_matchlist,
            "match": self.on_match,
        }
        self.bot = bot
        self.riot_key = self.bot.conf.get('Riot', 'key')
        self.robj = riot_api.RiotApi(self.bot.loop, self.riot_key)

    def unload(self):
        pass

    @asyncio.coroutine
    def on_rank(self, message, args):
        if len(args) < 1:
            yield from self.bot.send_message(message.channel, '**Error**: No summoner specified')

        response = ''

        name = ''.join([s.lower() for s in args])

        try:
            sobj = yield from self.robj.get_summoner_by_name([name])
            response += "*{}*\n**level**: {}\n".format(sobj[name]['name'], sobj[name]['summonerLevel'])
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                yield from self.bot.send_message(message.channel, '**Error**: Summoner not found')
                return
            else:
                raise e

        try:
            lobj = yield from self.robj.get_league_by_summonerid(sobj[name]['id'])
            rank = 'Unranked'
            for league in lobj[str(sobj[name]['id'])]:
                if league['queue'] == 'RANKED_SOLO_5x5':
                    rank = league['tier'].lower()
                    for summoner in league['entries']:
                        if summoner['playerOrTeamId'] == str(sobj[name]['id']):
                            rank += summoner['division']
            response += '**rank**: ' + rank + '\n'
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                response += '**rank**: Unranked\n'
            else:
                raise e

        yield from self.bot.send_message(message.channel, response)

    @asyncio.coroutine
    def on_matchlist(self,message,args):
        if len(args) < 1:
            yield from self.bot.send_message(message.channel, '**Error**: No summoner specified')

        response = ''

        name = ''.join([s.lower() for s in args])

        try:
            sobj = yield from self.robj.get_summoner_by_name([name])
            response += '**{}\'s Recent Match IDs: **\n```'.format(sobj[name]['name'])
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                yield from self.bot.send_message(message.channel, '**Error**: Summoner not found')
                return
            else:
                raise e


        matchlist = yield from self.robj.get_matchlist(summonerID=sobj[name]['id'])
        
        for i in range(10):
            current_match = matchlist["matches"][i]
            current_match_id = current_match['matchId']
            current_match_time = datetime.datetime.fromtimestamp(current_match['timestamp']/1000.0).strftime('%Y-%m-%d %I:%M %p')
            response += '{:10s} ({:10s})\n'.format(str(current_match_id),str(current_match_time))

        response += '```'
        yield from self.bot.send_message(message.channel, response)

    @asyncio.coroutine
    def on_match(self,message,args):
        if len(args) < 1:
            yield from self.bot.send_message(message.channel, '**Error**: No match id specified')

        match_id = ''.join([s.lower() for s in args])

        match = None
        all_champions = None

        try:
            match = yield from self.robj.get_match(matchID=match_id)
            all_champions = yield from self.robj.get_static_champion(region='na',dataById=True)
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                yield from self.bot.send_message(message.channel, '**Error**: Summoner not found')
                return
            else:
                raise e

        match_creation = datetime.datetime.fromtimestamp(match['matchCreation']/1000.0).strftime('%Y-%m-%d %I:%M %p')
        

        # Add participant ids, lanes, championId, k/d/a, gold, creep score, team id
        summoner_info = {
            100: {'TOP':[], 'JUNGLE':[], 'MIDDLE':[], 'BOTTOM':[]}, 
            200: {'TOP':[], 'JUNGLE':[], 'MIDDLE':[], 'BOTTOM':[]}
        }
        for participant in match['participants']:
            team_id = int(participant['teamId'])
            lane = participant['timeline']['lane']
            summoner_info[team_id][lane].append({
                'participant_id': participant['participantId'],
                'champion_id': participant['championId'],
                'kills': participant['stats']['kills'],
                'deaths': participant['stats']['deaths'],
                'assists': participant['stats']['assists'],
                'gold': participant['stats']['goldEarned'],
                'creep_score': participant['stats']['minionsKilled'],
                'summoner_name': '',
                'champion_name': all_champions['data'][str(participant['championId'])]['name']
            })

        # @TODO Make this less ugly, David.
        # Add in summoner names 
        for team_id in summoner_info:
            for lane in summoner_info[team_id]:
                for summoner in summoner_info[team_id][lane]:
                    for identity in match['participantIdentities']:
                        if summoner['participant_id'] == identity['participantId']:
                            summoner['summoner_name'] = identity['player']['summonerName']

        # Formulate response string
        response = '```'
        response += 'Match ID {:10} ({:10})\n'.format(match_id,match_creation)
        
        for team_id in summoner_info:
            response += 'Team {}\n'.format(team_id)
            for lane in summoner_info[team_id]:
                for summoner in summoner_info[team_id][lane]:  
                    response += '{:16} {:10} {}/{}/{} CS:{:3} Gold:{:5}\n'.format(
                            summoner['summoner_name'], summoner['champion_name'], summoner['kills'], 
                            summoner['deaths'], summoner['assists'], summoner['creep_score'], summoner['gold']
                    )
            response += '\n'
        response += '```'
        
        yield from self.bot.send_message(message.channel, response)
