from discord.ext import commands
import discord
from typing import Optional


class Context(commands.Context):
    def __init__(self, **kwargs: dict) -> None:
        super(Context, self).__init__(**kwargs)

    async def error(self, content: str, description: Optional[str] = None) -> discord.Message:
        embed = discord.Embed(title=f"\U000026a0 {content}", color=0xffc107)
        if description is not None:
            embed.description = description

        return await self.send(embed=embed)
