from discord.ext.commands import Cog, group, guild_only
from typing import TYPE_CHECKING
from more_itertools import chunked
import random
import discord
import numpy as np

from lib.context import Context

if TYPE_CHECKING:
    from bot import MiniMaid

BASE_TEAM_TEXT = """
**チーム分けの結果**
{0}チーム

{1}
"""


async def send_teams(ctx: Context, teams: list) -> discord.Message:
    team_text = ""
    for i, team in enumerate(teams, start=1):
        team_text += "チーム{0}: {1}\n\n".format(i, ' '.join(mem.mention for mem in team))

    text = BASE_TEAM_TEXT.format(len(teams), team_text)
    return await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())


class TeamCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot

    @group(invoke_without_command=True)
    @guild_only()
    async def team(self, ctx: Context, num: int, *, _members: str) -> None:
        """チーム分けを行うコマンドです。指定したチーム数にユーザーを分割します。everyoneと入力すると全員をチーム分けします。"""
        members = list(ctx.guild.members) if _members == "everyone" else list(ctx.message.mentions)
        if num > len(members):
            await ctx.send("チームの数はメンバーの人数より多くすることはできません。", reference=ctx.message)
            return

        random.shuffle(members)
        teams = np.array_split(members, num)
        await send_teams(ctx, teams)

    @team.command(name="chunked")
    async def by_member_count(self, ctx: Context, num: int, *, _members: str) -> None:
        """チームの人数を指定して分割します。everyoneと入力すると全員をチーム分けします。"""
        members = list(ctx.guild.members) if _members == "everyone" else list(ctx.message.mentions)
        random.shuffle(members)
        teams = list(chunked(members, num))
        await send_teams(ctx, teams)


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(TeamCog(bot))
