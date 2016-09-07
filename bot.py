import discord
import riot_api
import asyncio
import configparser

# not yet used
defaults = {
        }

class DiscordBot(discord.Client):
    def __init__(self, conf_file):
        super(DiscordBot, self).__init__()
        # commands
        self.commands = {
            "commands": self.outputCommands,
            "rank": self.on_rank,
        }

        # read config file
        self.conf = configparser.SafeConfigParser(defaults)
        self.conf.read(conf_file)
        self.discord_token = self.conf.get('Bot', 'discord_token')
        self.riot_key = self.conf.get('Riot', 'key')

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
                    print("Error running command: {}".format(e))

    @asyncio.coroutine
    def outputCommands(self, message, args):
        response = "```The commands are:\n"
        for cmd in self.commands:
            response = response + "!" + cmd + "\n"
        response = response + "```"
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

if __name__ == "__main__":
    bot = DiscordBot('bot.conf')
    bot.run()
