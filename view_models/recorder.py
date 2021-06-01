import asyncio
import io
import traceback
from typing import TYPE_CHECKING

import discord
from discord.ext.ui import ObservedObject, Published

from lib.context import Context
from models.recorder import RecorderModel

if TYPE_CHECKING:
    from bot import MiniMaid


class RecorderViewModel(ObservedObject):
    def __init__(self, bot: 'MiniMaid', ctx: Context):
        super().__init__()
        self.model = RecorderModel()
        self.bot = bot
        self.ctx = ctx
        self.error = None

        # 0 -> not started
        # 1 -> recording
        # 2 -> recorded
        # -1 -> can't record
        # -2 -> error
        # -3 -> already recording
        if ctx.guild.id in ctx.cog.recording_guilds:
            self.status = Published(-2)
        elif self.can_record():
            self.status = Published(0)
        else:
            self.status = Published(-1)

    def get_prefix(self):
        return self.ctx.prefix

    def can_record(self):
        return self.ctx.voice_client is not None

    async def record_start(self):
        try:
            self.status = 1
            self.ctx.cog.recording_guilds.append(self.ctx.guild.id)
            file: io.BytesIO = await self.ctx.voice_client.record()
            self.model.file = file
            self.status = 2
            await self.ctx.send(file=self.model.make_file())
            self.ctx.cog.recording_guilds.remove(self.ctx.guild.id)
        except Exception as e:
            self.error = traceback.format_exc()[:2000]
            self.status = -2

    async def record_stop(self, interaction: discord.Interaction):
        self.bot.dispatch('record_stop', None)
