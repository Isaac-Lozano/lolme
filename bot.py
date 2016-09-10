import discord
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
        }
        self.modules = {}

        # read config file
        self.conf = configparser.SafeConfigParser(defaults)
        self.conf.read(conf_file)
        self.discord_token = self.conf.get('Bot', 'discord_token')


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
            traceback.print_exc()
            return
        except AttributeError as e:
            yield from self.send_message(message.channel,
                                         '**Error**: Module "{}" malformed'.format(modname))
            traceback.print_exc()
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

if __name__ == '__main__':
    bot = DiscordBot('bot.conf')
    bot.run()
