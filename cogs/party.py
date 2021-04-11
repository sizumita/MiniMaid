from discord.ext.commands import Cog, Context, group, guild_only
from lib.database.models import Party
from lib.database.query import select_party, select_parties
from sqlalchemy import update
from typing import TYPE_CHECKING
import discord

if TYPE_CHECKING:
    from bot import MiniMaid

PARTY_HELP = """
`{0.prefix}party list` -> パーティ一覧を表示します。
"""


class PartyCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot

    @group(invoke_without_command=True, aliases=["pt"])
    @guild_only()
    async def party(self, ctx: Context) -> None:
        """パーティ用コマンドの一覧ヘルプを表示します。"""
        await ctx.send(PARTY_HELP.format(ctx))

    @party.command(name="list")
    async def party_list(self, ctx: Context):
        """全てのパーティを表示します。"""
        async with self.bot.db.Session() as session:
            result = await session.execute(select_parties(ctx.guild.id))
            parties = result.scalars().all()
        if not parties:
            await ctx.send("パーティはありません。", reference=ctx.message)
            return

        text = "```\nパーティー名 : 人数\n{}\n```".format(
            "\n".join(f"{party.name} : {len(party.members)}人" for party in parties))
        await ctx.send(text, reference=ctx.message)

    @party.command(name="create")
    async def create_party(self, ctx: Context, name: str):
        """パーティを作成します。"""
        async with self.bot.db.Session() as session:
            result = await session.execute(select_party(ctx.guild.id, name))
            if result.scalars().first() is not None:
                await ctx.send("その名前のパーティはすでに存在します。", reference=ctx.message)
                await session.rollback()
                return
            await session.commit()

            async with session.begin():
                party = Party(name=name, guild_id=ctx.guild.id, members=[ctx.author.id], owner_id=ctx.author.id)
                session.add(party)
        await ctx.send(f"パーティ: `{name}`を作成しました。", reference=ctx.message)

    @party.command(name="join", aliases=["j"])
    async def join_party(self, ctx: Context, name: str):
        """パーティに参加します。"""
        async with self.bot.db.Session() as session:
            result = await session.execute(select_party(ctx.guild.id, name))
            party = result.scalars().first()
            if party is None:
                await ctx.send("その名前のパーティは存在しません。", reference=ctx.message)
                await session.rollback()
                return
            elif ctx.author.id in party.members:
                await ctx.send("すでに参加しています。", reference=ctx.message)
                await session.rollback()
                return

            party.members.append(ctx.author.id)
            await session.commit()
        await ctx.send(f"パーティ: `{name}`に参加しました。", reference=ctx.message)

    @party.command(name="leave", aliases=["l", "left"])
    async def leave_party(self, ctx: Context, name: str):
        """パーティから離脱します。"""
        async with self.bot.db.Session() as session:
            result = await session.execute(select_party(ctx.guild.id, name))
            party = result.scalars().first()
            if party is None:
                await ctx.send("その名前のパーティは存在しません。", reference=ctx.message)
                await session.rollback()
                return
            elif ctx.author.id not in party.members:
                await ctx.send("そのパーティに参加していません。", reference=ctx.message)
                await session.rollback()
                return

            members = list(party.members)
            members.remove(ctx.author.id)
            await session.commit()
            stmt = update(Party).where(Party.id == party.id).values(members=members)
            await session.execute(stmt)
            await session.commit()

        await ctx.send(f"パーティ: `{name}`から離脱しました。", reference=ctx.message)

    @party.command(name="remove", aliases=["r", "delete"])
    async def remove_party(self, ctx: Context, name: str):
        """パーティを削除します。作成者もしくはサーバーの管理権限を持っているユーザーが可能です。"""
        async with self.bot.db.Session() as session:
            result = await session.execute(select_party(ctx.guild.id, name))
            party = result.scalars().first()
            if party is None:
                await ctx.send("その名前のパーティは存在しません。", reference=ctx.message)
                await session.rollback()
                return
            if party.owner_id == ctx.author.id:
                await session.delete(party)
            elif ctx.author.guild_permissions.manage_server:
                await session.delete(party)
            else:
                await ctx.send("そのパーティを削除する権限がありません。", reference=ctx.message)
                await session.rollback()
                return
            await session.commit()
            await ctx.send(f"パーティ: `{name}`を削除しました。", reference=ctx.message)

    @party.command(name="call")
    async def call_party_members(self, ctx: Context, name: str, *, text: str):
        """パーティメンバー全員にメンション付きメッセージを送信します。"""
        async with self.bot.db.Session() as session:
            result = await session.execute(select_party(ctx.guild.id, name))
            party = result.scalars().first()
            if party is None:
                await ctx.send("その名前のパーティは存在しません。", reference=ctx.message)
                await session.rollback()
                return
            elif ctx.author.id not in party.members:
                await ctx.send("そのパーティに参加していません。", reference=ctx.message)
                await session.rollback()
                return
            await session.commit()
        content = text + " {}".format(
            " ".join(
                ctx.guild.get_member(member).mention
                for member in party.members if ctx.guild.get_member(member) is not None
            )[:2000-len(text)]
        )
        await ctx.send(content, allowed_mentions=discord.AllowedMentions(everyone=False, users=True))


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(PartyCog(bot))
