import asyncio
import audioop
import io
import struct
import re
from functools import partial
from concurrent.futures import ThreadPoolExecutor

import discord

from lib.database.models import GuildVoicePreference, UserVoicePreference
from lib.jtalk import JTalk

english_compiled = re.compile(r"[a-zA-Z]+")


class TextToSpeechEngine:
    def __init__(self, loop: asyncio.AbstractEventLoop, guild_preference: GuildVoicePreference) -> None:
        self.loop = loop
        self.guild_preference = guild_preference
        self.least_user = None
        self.jtalk = JTalk()
        self.jtalk_lock = asyncio.Lock()
        self.executor = ThreadPoolExecutor()

    def update_guild_preference(self, new_preference: GuildVoicePreference) -> None:
        self.guild_preference = new_preference

    def get_source(self, text: str):
        pcm = self.jtalk.generate_pcm(text)
        bin_pcm = struct.pack("h" * len(pcm), *pcm)
        return io.BytesIO(audioop.tostereo(bin_pcm, 2, 1, 1))

    async def generate_source(self,
                              message: discord.Message,
                              user_preference: UserVoicePreference,
                              english_dict: dict) -> discord.PCMAudio:
        read_name = all((
            True if self.least_user == message.author.id else False,
            self.guild_preference.read_name
        ))
        text = message.clean_content
        if read_name:
            if self.guild_preference.read_nick:
                text = message.author.nick + text
            else:
                text = message.author.name + text
        sentences = english_compiled.findall(text)
        for sentence in sentences:
            if sentence.upper() in english_dict.keys():
                text = text.replace(sentence, english_dict[sentence.upper()])

        async with self.jtalk_lock:
            self.jtalk.set_speed(user_preference.speed)
            self.jtalk.set_tone(user_preference.tone)
            self.jtalk.set_intone(user_preference.intone)
            self.jtalk.set_volume(user_preference.volume)
            r = await self.loop.run_in_executor(self.executor, partial(self.get_source, text))
            return discord.PCMAudio(r)
