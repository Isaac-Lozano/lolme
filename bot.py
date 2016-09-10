import discord
import riot_api
import overwatch_api
import asyncio
import configparser
import traceback
import datetime
import importlib

# not yet used
defaults = {
        }

class DiscordBot(discord.Client):
    def __init__(self, conf_file):
        super(DiscordBot, self).__init__()
        # commands
        self.commands = {
            "load": self.load_module,
            "unload": self.unload_module,
            "list_modules": self.list_modules,
            "commands": self.output_commands,
            "overwatch": self.overwatch_get_player_info,
            "overwatch_hero": self.overwatch_get_hero_info,
            "rank": self.on_rank,
            "matchlist":self.on_matchlist,
            "match":self.on_match
        }
        self.modules = {}

        # read config file
        self.conf = configparser.SafeConfigParser(defaults)
        self.conf.read(conf_file)
        self.discord_token = self.conf.get('Bot', 'discord_token')
        self.riot_key = self.conf.get('Riot', 'key')

        # overwatch api
        self.overwatchobj = overwatch_api.OverwatchApi(self.loop)
        # riot api
        self.robj = riot_api.RiotApi(self.loop, self.riot_key)

    # Override run() so we can remove the required parameter
    def run(self):
        super(DiscordBot, self).run(self.discord_token)

    @asyncio.coroutine
    def on_ready(self):
        print("logged in as {}".format(self.user.name))
        print(self.user.id)
        print("----------")

    @asyncio.coroutine
    def on_message(self, message):
        msg = message.content

        print(message.content)
        print("----------")

        if msg.startswith("!"):
            msg = msg[1:] # strip off the bang
            msg_split = msg.split(' ', 1)

            cmd = msg_split[0]
            if len(msg_split) != 2:
                args = []
            else:
                args = msg_split[1].split()

            if cmd in self.commands:
                try:
                    yield from self.commands[cmd](message, args)
                except Exception as e:
                    yield from self.send_message(message.channel, "Error running command")
                    traceback.print_exc()

    @asyncio.coroutine
    def load_module(self, message, args):
        if len(args) < 1:
            yield from self.send_message(message.channel, '**Error**: No module specified')
            return

        modname = args[0]

        try:
            importlib.invalidate_caches()
            module = importlib.import_module("modules." + modname)
            klass = getattr(module, modname)
            instance = klass(self)
            modcmds = instance.commands
            if not callable(instance.unload):
                raise AttributeError()
        except ImportError as e:
            yield from self.send_message(message.channel,
                                         '**Error**: Module "{}" not found'.format(modname))
            return
        except AttributeError as e:
            yield from self.send_message(message.channel,
                                         '**Error**: Module "{}" malformed'.format(modname))
            return

        for cmd in modcmds:
            if cmd in self.commands:
                yield from self.send_message(
                    message.channel,
                    '**Error**: Command conflict in "{}": !{}'.format(modname, cmd))
                instance.unload()
                return

        self.modules.update({modname: instance})
        self.commands.update(modcmds)
        yield from self.send_message(message.channel,
                                     'Module "{}" succesfully loaded'.format(modname))

    @asyncio.coroutine
    def unload_module(self, message, args):
        if len(args) < 1:
            yield from self.send_message(message.channel, '**Error**: No module specified')
            return

        modname = args[0]
        if modname not in self.modules:
            yield from self.send_message(message.channel,
                                         '**Error**: Module "{}" not currently loaded'.format(modname))
            return

        for cmd in self.modules[modname].commands:
            self.commands.pop(cmd)

        self.modules.pop(modname).unload()
        yield from self.send_message(message.channel,
                                     'Module "{}" succesfully unloaded'.format(modname))

    @asyncio.coroutine
    def list_modules(self, message, args):
        response = '```\n'
        response += 'loaded modules:\n'
        for module in self.modules:
            response += module + '\n'
        response += '```'
        yield from self.send_message(message.channel, response)

    @asyncio.coroutine
    def output_commands(self, message, args):
        response = "```The commands are:\n"
        for cmd in self.commands:
            response = response + "!" + cmd + "\n"
        response = response + "```"
        yield from self.send_message(message.channel, response)

    @asyncio.coroutine
    def overwatch_get_player_info(self, message, args):
        overwatch_profile_response = ''
        overwatch_hero_response = ''

        name = args[0]

        try:
            overwatch_profile_response = yield from self.overwatchobj.get_player_profile(name)
            overwatch_hero_response = yield from self.overwatchobj.get_player_hero_info(name)
        except overwatch_api.OverwatchApiHttpException as e:
            if e.response == 404:
                yield from self.send_message(message.channel, '**Error**: Player not found')
                return
            else:
                raise e

        player_level = overwatch_profile_response['data']['level']
        player_rank = int(overwatch_profile_response['data']['competitive']['rank'])
        player_wins = int(overwatch_profile_response['data']['games']['competitive']['wins'])
        player_played = int(overwatch_profile_response['data']['games']['competitive']['played'])
        player_win_rate = player_wins/player_played
        player_win_rate = str(int(round(player_win_rate, 2) * 100)) + "%"
        amount_of_time_played = overwatch_profile_response['data']['playtime']['quick']

        most_played_hero = overwatch_hero_response[0]['name']
        most_played_hero_playtime = overwatch_hero_response[0]['playtime']

        # API is inconsistent with naming. This fixes the issue.
        if most_played_hero == 'Soldier: 76':
            most_played_hero = 'Soldier76'

        response = "```{}:\n".format(name)
        response += "Player Level: {}\n".format(player_level)
        response += "Player Competitive Rank: {}\n".format(player_rank)
        response += "Player Competitive Win Rate: {}\n".format(player_win_rate)
        response += "Played QuickPlay for: {}\n".format(amount_of_time_played)
        response += "Most Played Hero: {} ({})\n```".format(most_played_hero, most_played_hero_playtime)
        
        yield from self.send_message(message.channel, response)

    @asyncio.coroutine
    def overwatch_get_hero_info(self, message, args):
        specific_hero_response = ''
        name = args[0]
        print(name)
        hero = args[1]
        print(hero)

        try:
            specific_hero_response = yield from self.overwatchobj.get_specific_hero_info(name, hero)
        except overwatch_api.OverwatchApiHttpException as e:
            if e.response == 404:
                yield from self.send_message(message.channel, '**Error**: Player/Hero not found')
                return
            else:
                raise e
        win_rate = specific_hero_response[hero]['WinPercentage']
        games_played = specific_hero_response[hero]['GamesPlayed']

        response = "```{} Info:\n".format(hero)
        response += "Competitive Win Percentage: {}\n".format(win_rate)
        response += "Competitive Games Played: {}\n".format(games_played)
        response += "```"

        yield from self.send_message(message.channel, response)



    @asyncio.coroutine
    def on_rank(self, message, args):
        if len(args) < 1:
            yield from self.send_message(message.channel, '**Error**: No summoner specified')

        response = ''

        name = ''.join([s.lower() for s in args])

        try:
            sobj = yield from self.robj.get_summoner_by_name([name])
            response += "*{}*\n**level**: {}\n".format(sobj[name]['name'], sobj[name]['summonerLevel'])
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                yield from self.send_message(message.channel, '**Error**: Summoner not found')
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

        yield from self.send_message(message.channel, response)

    @asyncio.coroutine
    def test_fxn(self,message,args):
        yield from self.send_message(message.channel, "Ddayknight is gold 1, don't judge @OnVar#4902")

    @asyncio.coroutine
    def on_matchlist(self,message,args):
        if len(args) < 1:
            yield from self.send_message(message.channel, '**Error**: No summoner specified')

        response = ''

        name = ''.join([s.lower() for s in args])

        try:
            sobj = yield from self.robj.get_summoner_by_name([name])
            response += '**{}\'s Recent Match IDs: **\n```'.format(sobj[name]['name'])
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                yield from self.send_message(message.channel, '**Error**: Summoner not found')
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
        yield from self.send_message(message.channel, response)

    @asyncio.coroutine
    def on_match(self,message,args):
        if len(args) < 1:
            yield from self.send_message(message.channel, '**Error**: No match id specified')

        match_id = ''.join([s.lower() for s in args])

        match = None
        all_champions = None

        try:
            match = yield from self.robj.get_match(matchID=match_id)
            all_champions = yield from self.robj.get_static_champion(region='na',dataById=True)
        except riot_api.RiotApiHttpException as e:
            if e.response == 404:
                yield from self.send_message(message.channel, '**Error**: Summoner not found')
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
        
        yield from self.send_message(message.channel, response)


if __name__ == '__main__':
    bot = DiscordBot('bot.conf')
    bot.run()
