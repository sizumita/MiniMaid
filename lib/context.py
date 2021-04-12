from discord.ext import commands
import discord


class Context(commands.Context):
    def __init__(self, **kwargs):
        super(Context, self).__init__(**kwargs)

    async def error(self, content, description=None):
        embed = discord.Embed(title=f"\U000026a0 {content}", color=0xffc107)
        if description is not None:
            embed.description = description

        await self.send(embed=embed)
