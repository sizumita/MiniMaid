from discord.ext import commands
import discord

from lib.database.database import Database


class MiniMaid(commands.Bot):
    def __init__(self):
        super(MiniMaid, self).__init__(
            command_prefix="",
            intents=discord.Intents.all(),
            help_command=None
        )
        self.db = Database()

    async def start(self, *args, **kwargs):
        await self.db.start()
        await super(MiniMaid, self).start(*args, **kwargs)
