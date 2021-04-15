from os import environ

from discord.ext import commands
import discord

from lib.database.database import Database
from lib.context import Context
from lib.errors import MiniMaidException


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

    async def on_command_error(self, context: Context, exception: Exception) -> None:
        if isinstance(exception, commands.CommandNotFound):
            pass

        elif isinstance(exception, commands.BadArgument):
            await context.error("引数の解析に失敗しました。", "引数を確認して再度コマンドを実行してください。")

        elif isinstance(exception, MiniMaidException):
            await context.error(exception.message())

        elif isinstance(exception, commands.NoPrivateMessage):
            await context.error("このコマンドはサーバー専用です。")

        else:
            await super(MiniMaid, self).on_command_error(context, exception)

    async def start(self, *args: list, **kwargs: dict) -> None:
        await self.db.start()
        await super(MiniMaid, self).start(*args, **kwargs)

    async def process_commands(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)
