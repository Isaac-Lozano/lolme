import asyncio
import overwatch_api

class OverwatchMod(object):
    def __init__(self, bot):
        self.commands = {
            "overwatch": self.overwatch_get_player_info,
            "overwatch_hero": self.overwatch_get_hero_info,
        }
        self.bot = bot
        self.overwatchobj = overwatch_api.OverwatchApi(self.bot.loop)

    def unload(self):
        pass

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
                yield from self.bot.send_message(message.channel, '**Error**: Player not found')
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
        
        yield from self.bot.send_message(message.channel, response)

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
                yield from self.bot.send_message(message.channel, '**Error**: Player/Hero not found')
                return
            else:
                raise e
        win_rate = specific_hero_response[hero]['WinPercentage']
        games_played = specific_hero_response[hero]['GamesPlayed']

        response = "```{} Info:\n".format(hero)
        response += "Competitive Win Percentage: {}\n".format(win_rate)
        response += "Competitive Games Played: {}\n".format(games_played)
        response += "```"

        yield from self.bot.send_message(message.channel, response)
