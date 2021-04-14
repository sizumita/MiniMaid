from discord.ext import commands
import discord
from os import environ

from lib.database.database import Database
from lib.context import Context


class MiniMaid(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        super(MiniMaid, self).__init__(
            command_prefix=commands.when_mentioned_or(environ["PREFIX"]),
            intents=intents,
            help_command=None
        )
        self.db = Database()

    async def on_command_error(self, context: Context, exception: Exception):
        if isinstance(exception, commands.CommandNotFound):
            return
        if isinstance(exception, commands.BadArgument):
            await context.error("引数の解析に失敗しました。", "引数を確認して再度コマンドを実行してください。")
            return
        await super(MiniMaid, self).on_command_error(context, exception)

    async def start(self, *args: list, **kwargs: dict) -> None:
        await self.db.start()
        await super(MiniMaid, self).start(*args, **kwargs)

    async def process_commands(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)
