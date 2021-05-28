import asyncio
from typing import TYPE_CHECKING
import math

import discord
from discord.ext.ui import ObservedObject, Published

from lib.context import Context
from lib.tag_attachment import TagAttachment

if TYPE_CHECKING:
    from cogs.audio import AudioBase
    from bot import MiniMaid


class AudioTagViewModel(ObservedObject):
    def __init__(self, bot: 'MiniMaid', cog: 'AudioBase', ctx: Context, tags: list):
        super().__init__()
        self.cog = cog
        self.ctx = ctx
        self.is_playing = Published(False)
        self.page = Published(0)
        self.file = None
        self.tags = tags
        self.bot = bot
        self.max_page = math.ceil(len(self.tags) / 5) if len(self.tags) > 5 else 0

    def next_page(self, interaction: discord.Interaction):
        if self.page < self.max_page:
            self.page += 1

    def priv_page(self, interaction: discord.Interaction):
        if self.page != 0:
            self.page -= 1

    def get_tags(self):
        return self.tags[self.page * 5: (self.page + 1) * 5]

    async def skip(self, interaction: discord.Interaction):
        self.bot.dispatch("skip", self.ctx)

    async def play(self, interaction: discord.Interaction, index: int):
        tag = self.get_tags()[index]
        file = TagAttachment(tag)
        source = await self.cog.engine.create_source(file)

        async with self.cog.locks[self.ctx.guild.id]:
            if self.ctx.guild.voice_client is None:
                return

            def check(ctx2: Context) -> bool:
                return ctx2.channel.id == self.ctx.channel.id

            event = asyncio.Event(loop=self.bot.loop)
            self.file = file
            self.is_playing = True
            self.ctx.voice_client.play(source, after=lambda x: event.set())

        async def wait_end():
            for coro in asyncio.as_completed([event.wait(), self.bot.wait_for("skip", check=check, timeout=None)]):
                result = await coro
                if isinstance(result, Context):
                    self.ctx.voice_client.stop()
                break

            self.is_playing = False
            self.file = None

        self.bot.loop.create_task(wait_end())
