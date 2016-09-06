import discord
import asyncio

class DiscordBot(discord.Client):
    def __init__(self):
        super(DiscordBot, self).__init__()
        self.commands = {
        "commands": self.outputCommands,
		"music": self.on_yt,
                }
        self.player_map = {}

    async def on_ready(self):
        print("logged in as {}".format(self.user.name))
        print(self.user.id)
        print("----------")

    async def on_message(self, message):
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
                    await self.commands[cmd](message, args)
                except Exception as e:
                    await self.send_message(message.channel, "Error running command")
                    print("Error runninc command: {}".format(e))

    async def outputCommands(self, message, args):
        response = "```The commands are:\n"
        for cmd in self.commands:
            response = response + "!" + cmd + "\n"
        response = response + "```"
        await self.send_message(message.channel, response)

    async def on_yt(self, message, args):
        if len(args) > 0:
            if args[0] == 'play':
                if len(args) > 1:
                    url = args[1]
                    voice = message.author.voice_channel
                    if voice:
                        if self.is_voice_connected(message.server):
                            vc = self.voice_client_in(message.server)
                            await vc.move_to(voice)
                        else:
                            vc = await self.join_voice_channel(voice)
                        if vc in self.player_map:
                            self.player_map[vc].stop()
                        player = await vc.create_ytdl_player(url)
                        self.player_map[vc] = player
                        player.start()
                else:
                    await self.send_message(message.channel, "No url specified")
            elif args[0] == 'stop':
                if self.is_voice_connected(message.server):
                    self.player_map[self.voice_client_in(message.server)].stop()
            else:
                await self.send_message(message.channel, "bad operation")
        else:
            await self.send_message(message.channel, "No operation specified")

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run('MjAwNDI4OTgwNDcyNTEyNTEy.Cl9KGw.UJTnD1BpHs83XHEzVt2mP-Rw7JQ')
