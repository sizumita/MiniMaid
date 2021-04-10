from discord.ext import commands
import discord
from os import environ

from lib.database.database import Database


class MiniMaid(commands.Bot):
    def __init__(self) -> None:
        super(MiniMaid, self).__init__(
            command_prefix=commands.when_mentioned_or(environ["PREFIX"]),
            intents=discord.Intents.all(),
            help_command=None
        )
        self.db = Database()

    async def start(self, *args: list, **kwargs: dict) -> None:
        await self.db.start()
        await super(MiniMaid, self).start(*args, **kwargs)
