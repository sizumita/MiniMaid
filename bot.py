from discord.ext import commands
import discord
from sqlalchemy.future import select

from lib.database.database import Database
from lib.database.models import Preference


class MiniMaid(commands.Bot):
    def __init__(self) -> None:
        super(MiniMaid, self).__init__(
            command_prefix="",
            intents=discord.Intents.all(),
            help_command=None
        )
        self.db = Database()

    async def start(self, *args: list, **kwargs: dict) -> None:
        await self.db.start()
        await super(MiniMaid, self).start(*args, **kwargs)

    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None:
            return

        async with self.db.Session() as session:
            sql = select(Preference).where(Preference.guild_id == message.guild.id)
            result = await session.execute(sql)
            data = result.scalars().first()
            if data is None:
                return

        if data.command_channel_id != message.channel.id:
            return

        await self.process_commands(message)
