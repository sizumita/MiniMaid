from discord.ext.commands import (
    Cog,
    Context,
    group
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bot import MiniMaid


class PollCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(PollCog(bot))
