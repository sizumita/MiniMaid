from typing import TYPE_CHECKING

from discord.ext.commands import (
    Cog,
    group
)

from lib.context import Context
from lib.embed import help_embed

if TYPE_CHECKING:
    from bot import MiniMaid


class HelpCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot

    @group(name="help", invoke_without_command=True)
    async def help_command(self, ctx: Context) -> None:
        await ctx.embed(help_embed())

    @group(name="ping", invoke_without_command=True)
    async def ping(self, ctx: Context) -> None:
        await ctx.success("pong!")


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(HelpCog(bot))
