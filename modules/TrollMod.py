import asyncio

gif_link_map = {
    "thresh": "http://i.imgur.com/75xQfzE.gif"
    "zilean": "http://i.imgur.com/HFPyl6Y.gif"
}

upsidedown_map = {
    'a': 'ɐ',
    'b': 'q',
    'c': 'ɔ',
    'd': 'p',
    'e': 'ǝ',
    'f': 'ɟ',
    'g': 'ƃ',
    'h': 'ɥ',
    'i': 'ᴉ',
    'j': 'ɾ',
    'k': 'ʞ',
    'l': 'l',
    'm': 'ɯ',
    'n': 'u',
    'o': 'o',
    'p': 'd',
    'q': 'b',
    'r': 'ɹ',
    's': 's',
    't': 'ʇ',
    'u': 'n',
    'v': 'ʌ',
    'w': 'ʍ',
    'x': 'x',
    'y': 'ʎ',
    'z': 'z',
    'A': '∀',
    'B': 'B',
    'C': 'Ɔ',
    'D': 'D',
    'E': 'Ǝ',
    'F': 'Ⅎ',
    'G': 'פ',
    'H': 'H',
    'I': 'I',
    'J': 'ſ',
    'K': 'ʞ',
    'L': '˥',
    'M': 'W',
    'N': 'N',
    'O': 'O',
    'P': 'Ԁ',
    'Q': 'Q',
    'R': 'ɹ',
    'S': 'S',
    'T': '┴',
    'U': '∩',
    'V': 'Λ',
    'W': 'M',
    'X': 'X',
    'Y': '⅄',
    'Z': 'Z',
    '0': '0',
    '1': 'Ɩ',
    '2': 'ᄅ',
    '3': 'Ɛ',
    '4': 'ㄣ',
    '5': 'ϛ',
    '6': '9',
    '7': 'ㄥ',
    '8': '8',
    '9': '6',
    ',': '\'',
    '.': '˙',
    '?': '¿',
    '!': '¡',
    '"': ',,',
    '\'': ',',
    '`': ',',
    '(': ')',
    ')': '(',
    '[': ']',
    ']': '[',
    '{': '}',
    '}': '{',
    '<': '>',
    '>': '<',
    '&': '⅋',
    '_': '‾',
}

class TrollMod(object):
    def __init__(self, bot):
        self.commands = {
            "flip": self.on_flip,
            "unflip": self.on_unflip,
            "gif": self.on_gif,
        }
        self.bot = bot

    def unload():
        pass

    @asyncio.coroutine
    def on_flip(self, message, args):
        msg = ' '.join(args)
        msg = msg[::-1]
        updown = ''
        for ch in msg:
            try:
                updown += upsidedown_map[ch]
            except KeyError:
                updown += ch
        yield from self.bot.send_message(message.channel, '(ノ°Д°）ノ︵ ' + updown)

    @asyncio.coroutine
    def on_unflip(self, message, args):
        msg = ' '.join(args)
        yield from self.bot.send_message(message.channel, msg + ' ノ( ゜-゜ノ)')

    @asyncio.coroutine
    def on_gif(self, message, args):
        msg = ' '.join(args)
        gif_link = gif_link_map[msg]
        yield from self.bot.send_message(message.channel, gif_link)
        
