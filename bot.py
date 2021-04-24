import sys
from os import environ
from typing import Any

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

    async def on_ready(self) -> None:
        prefix = environ["PREFIX"]
        await self.change_presence(activity=discord.Game(name=f"prefix: {prefix}"))

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        _, err, _ = sys.exc_info()
        if isinstance(err, MiniMaidException) and event_method == "on_message":
            embed = discord.Embed(title=f"\U000026a0 {err.message()}", color=0xffc107)

            message = args[0]
            await message.channel.send(embed=embed)
            return

        await super(MiniMaid, self).on_error(event_method, *args, **kwargs)

    async def on_command_error(self, context: Context, exception: Exception) -> None:
        if isinstance(exception, commands.CommandNotFound):
            pass

        elif isinstance(exception, commands.BadArgument):
            await context.error("引数の解析に失敗しました。", "引数を確認して再度コマンドを実行してください。")

        elif isinstance(exception, MiniMaidException):
            await context.error(exception.message())

        elif isinstance(exception, commands.NoPrivateMessage):
            await context.error("このコマンドはサーバー専用です。")

        elif isinstance(exception, commands.CommandOnCooldown):
            await context.error(f"クールダウン中です。{int(exception.retry_after)}秒待ってから実行してください。")

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
