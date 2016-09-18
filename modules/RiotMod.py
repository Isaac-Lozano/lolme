import asyncio
import riot_api
import datetime
import operator 

class RiotMod(object):
    def __init__(self, bot):
        self.commands = {
            #"rank": self.on_rank,
            "summoner": self.on_summoner,
            "matchlist": self.on_matchlist,
            "match": self.on_match,
            "livematch": self.on_livematch
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
    def on_summoner(self, message, args):
        if len(args) < 1:
            yield from self.bot.send_message(message.channel, '**Error**: No summoner specified')

        response = ''

        name = ''.join([s.lower() for s in args])

        # Get a summoner object from the riot api in order to get a summoner level.
        try:
            sobj = yield from self.robj.get_summoner_by_name([name])
            response += "*{}*\n**Level**: {}\n".format(sobj[name]['name'], sobj[name]['summonerLevel'])
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                yield from self.bot.send_message(message.channel, '**Error**: Summoner not found')
                return
            else:
                raise e

        # Get a league object from the riot api in order to get the summoner rank.
        try:
            lobj = yield from self.robj.get_league_by_summonerid(sobj[name]['id'])
            rank = 'Unranked'
            for league in lobj[str(sobj[name]['id'])]:
                if league['queue'] == 'RANKED_SOLO_5x5':
                    rank = league['tier'].lower()
                    for summoner in league['entries']:
                        if summoner['playerOrTeamId'] == str(sobj[name]['id']):
                            rank += summoner['division']
            response += '**Rank**: ' + rank + '\n'
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                response += '**rank**: Unranked\n'
            else:
                raise e

        # Get ranked stats object from the riot api.
        try:
            rsobj = yield from self.robj.get_stats_ranked(summonerID=sobj[name]['id'])
            all_champions = yield from self.robj.get_static_champion(region='na',dataById=True)
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                yield from self.bot.send_message(message.channel, '**Error**: Summoner not found')
                return
            else:
                raise e

        # Sum up total games played for that particular summoner.
        total_games_played = sum([champ['stats']['totalSessionsPlayed'] for champ in rsobj['champions']])

        # Get total games played per champion. Get the top 5 most played champions.  
        champs_num_games = {all_champions['data'][str(champ['id'])]['name']:champ['stats']['totalSessionsPlayed'] for champ in rsobj['champions'] if champ['id'] is not 0}
        sorted_num_games = sorted(champs_num_games.items(), key=operator.itemgetter(1))[-5:]
        most_played_champs = ', '.join([game[0] for game in sorted_num_games])
        response += '**Most Played Champions**: {}\n'.format(most_played_champs)

        # Get win rates per champion. Get the top 5 most winning champions.
        champs_winrates = {
            all_champions['data'][str(champ['id'])]['name']:champ['stats']['totalSessionsWon']/float(champ['stats']['totalSessionsPlayed']) 
            for champ in rsobj['champions'] if champ['id'] is not 0 and champ['stats']['totalSessionsPlayed'] > (float(total_games_played)*0.02)
        }
        sorted_winrates = sorted(champs_winrates.items(), key=operator.itemgetter(1))[-5:]
        most_winning_champs = ', '.join([game[0] for game in sorted_winrates])
        response += '**Most Winning Champions**: {}\n'.format(most_winning_champs)

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

        # Get match creation datetime
        match_creation = datetime.datetime.fromtimestamp(match['matchCreation']/1000.0).strftime('%Y-%m-%d %I:%M %p')

        # Get match winner
        team_win_status = {'Blue': 'Lost', 'Red': 'Lost'}
        winning_team_id = 'Blue' if match['teams'][0]['winner'] is True and match['teams'][0]['teamId'] == 100 else 'Red'
        team_win_status[winning_team_id] = 'Won'

        # Add participant ids, lanes, championId, k/d/a, gold, creep score, team id
        summoner_info = {
            'Blue': {'TOP':[], 'JUNGLE':[], 'MIDDLE':[], 'BOTTOM':[]}, 
            'Red': {'TOP':[], 'JUNGLE':[], 'MIDDLE':[], 'BOTTOM':[]}
        }

        # Get summoner names separately
        summoner_names = {identity['participantId']: identity['player']['summonerName'] for identity in match['participantIdentities']}

        for participant in match['participants']:
            team_id = 'Blue' if participant['teamId'] == 100 else 'Red'
            lane = participant['timeline']['lane']
            summoner_info[team_id][lane].append({
                'participant_id': participant['participantId'],
                'champion_id': participant['championId'],
                'kills': participant['stats']['kills'],
                'deaths': participant['stats']['deaths'],
                'assists': participant['stats']['assists'],
                'gold': participant['stats']['goldEarned'],
                'creep_score': participant['stats']['minionsKilled'],
                'summoner_name': summoner_names[participant['participantId']],
                'champion_name': all_champions['data'][str(participant['championId'])]['name']
            })

        # Formulate response string
        response = '**Match ID: {}** *({})*\n'.format(match_id,match_creation)
        response += '```'
        
        for team_id in summoner_info:
            response += 'Team {} - {}\n'.format(team_id, team_win_status[team_id])
            for lane in summoner_info[team_id]:
                for summoner in summoner_info[team_id][lane]:  
                    response += '{:16} {:10} {}/{}/{} CS:{:3} Gold:{:5}\n'.format(
                            summoner['summoner_name'], summoner['champion_name'], summoner['kills'], 
                            summoner['deaths'], summoner['assists'], summoner['creep_score'], summoner['gold']
                    )
            response += '\n'
        response += '```'
        
        yield from self.bot.send_message(message.channel, response)

    @asyncio.coroutine
    def on_livematch(self,message,args):
        if len(args) < 1:
            yield from self.bot.send_message(message.channel, '**Error**: No summoner name specified')

        summoner_name = ''.join([s.lower() for s in args])

        try:
            summoner = yield from self.robj.get_summoner_by_name(summoner_names=[summoner_name])
            match = yield from self.robj.get_live_match(summonerID=summoner[summoner_name]['id'])
            all_champions = yield from self.robj.get_static_champion(region='na',dataById=True)
            all_summoner_spells = yield from self.robj.get_static_summoner_spell(region='na',dataById=True,spellData='all')
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                yield from self.bot.send_message(message.channel, '**Error**: Summoner not found')
                return
            else:
                raise e

        # Get match creation datetime
        match_creation = datetime.datetime.fromtimestamp(match['gameStartTime']/1000.0).strftime('%Y-%m-%d %I:%M %p')

        # Get match length (so far)
        minutes, seconds = divmod(match['gameLength'], 60)
        hours, minutes = divmod(minutes, 60)
        match_length = "{}:{}:{}".format(hours,minutes,seconds) if hours > 0 else "{}:{}".format(minutes,seconds)

        # Add summoner names, champion names
        summoner_info = {
            'Blue': [], 
            'Red': []
        }

        for summoner in match['participants']:
            team = 'Blue' if summoner['teamId'] == 100 else 'Red'
            summoner_info[team].append({
                'summoner_name':summoner['summonerName'],
                'champion_name':all_champions['data'][str(summoner['championId'])]['name'],
                'summoner_spell1':all_summoner_spells['data'][str(summoner['spell1Id'])]['name'],
                'summoner_spell2':all_summoner_spells['data'][str(summoner['spell2Id'])]['name']
            })

        # Formulate response string
        response = '**Match ID: {}** *({})*\n'.format(match['gameId'],match_creation)
        response += '```'
        response += 'Match Time: {}\n'.format(match_length)
        for team in summoner_info:
            response += 'Team {}\n'.format(team)
            for summoner in summoner_info[team]:  
                response += '{:16} {:16} {:9} {:9}\n'.format(
                        summoner['summoner_name'], summoner['champion_name'], summoner['summoner_spell1'], summoner['summoner_spell2']
                )
            response += '\n'
        response += '```'
        
        yield from self.bot.send_message(message.channel, response)
