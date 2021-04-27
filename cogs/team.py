from typing import TYPE_CHECKING
import random
import discord

import numpy as np
from more_itertools import chunked
from discord.ext.commands import Cog, group, guild_only

from lib.context import Context
from lib.errors import UserNotConnected


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


def get_members(ctx: Context, _members: str) -> list:
    if _members == "everyone":
        return [m for m in ctx.guild.members if not m.bot]
    elif _members in ["vc", "voice"]:
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            raise UserNotConnected()
        return [m for m in ctx.author.voice.channel.members if not m.bot]

    return list(ctx.message.mentions)


class TeamCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot

    @group(invoke_without_command=True)
    @guild_only()
    async def team(self, ctx: Context, num: int, *, _members: str) -> None:
        """チーム分けを行うコマンドです。指定したチーム数にユーザーを分割します。everyoneと入力すると全員をチーム分けします。"""
        members = get_members(ctx, _members)
        if num > len(members):
            await ctx.send("チームの数はメンバーの人数より多くすることはできません。", reference=ctx.message)
            return

        random.shuffle(members)
        teams = np.array_split(members, num)
        await send_teams(ctx, teams)

    @team.command(name="chunked")
    async def by_member_count(self, ctx: Context, num: int, *, _members: str) -> None:
        """チームの人数を指定して分割します。everyoneと入力すると全員をチーム分けします。"""
        members = get_members(ctx, _members)
        random.shuffle(members)
        teams = list(chunked(members, num))
        await send_teams(ctx, teams)


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(TeamCog(bot))
