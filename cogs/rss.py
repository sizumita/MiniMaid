from typing import TYPE_CHECKING
import re

from discord.ext.commands import (
    Cog,
    group
)
import aiohttp
import feedparser
import discord

from lib.rss.scheduler import FeedScheduler
from lib.context import Context
from lib.database.models import Feed, Reader
from lib.database.query import select_feed, select_reader, select_reader_by_id, select_reader_by_channel_id

if TYPE_CHECKING:
    from bot import MiniMaid

url_compiled = re.compile(r"^https?://[\w!?/+\-_~=;.,*&@#$%()'\[\]]+$")


class RSSCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot
        self.scheduler = FeedScheduler(self.bot)

    def cog_unload(self) -> None:
        self.scheduler.task.cancel()

    @group(invoke_without_command=True)
    async def rss(self, ctx: Context) -> None:
        async with self.bot.db.Session() as session:
            result = await session.execute(select_reader_by_channel_id(ctx.channel.id))
            readers = result.scalars().all()
            if not readers:
                await ctx.error("このチャンネルではRSSは登録されていません。")
                return
            await session.commit()
        embed = discord.Embed(
            title="RSS一覧",
            colour=discord.Colour.dark_orange()
        )
        embed.description = "**ID : URL**\n" + "\n".join([f"**{reader.id}**: {reader.feed.url}" for reader in readers])
        embed.set_footer(text=f"{ctx.prefix}rss remove <RSSのID> で削除できます。")

        await ctx.embed(embed)

    @rss.command(name="add")
    async def add_rss(self, ctx: Context, url: str) -> None:
        match = url_compiled.match(url)
        if match is None:
            await ctx.error("URLの形式が正しくありません。")
            return
        async with aiohttp.ClientSession() as http_session:
            async with http_session.get(url) as response:
                if response.status >= 400:
                    await ctx.error("URLが無効です。")
                    return
                raw_data = await response.text()
            data = feedparser.parse(raw_data)
            if not data.version:
                await ctx.error("URLから取得したデータのタイプがRSSのものではありませんでした。")
                return
        async with self.bot.db.SerializedSession() as session:
            result = await session.execute(select_feed(url))
            f = result.scalars().first()
            if f is None:
                f = Feed(url=url)
                session.add(f)
            await session.commit()
            result2 = await session.execute(select_reader(f.id, ctx.channel.id))
            r = result2.scalars().first()
            if r is not None:
                await ctx.error("すでに存在しています。")
                await session.rollback()
                return

            session.add(Reader(feed_id=f.id, channel_id=ctx.channel.id, owner_id=ctx.author.id))
            await session.commit()
        await ctx.success("RSSの配信を設定しました。")

    @rss.command(name="remove", aliases=["rm", "delete"])
    async def remove_rss(self, ctx: Context, rss_id: int) -> None:
        async with self.bot.db.SerializedSession() as session:
            result = await session.execute(select_reader_by_id(rss_id))
            reader = result.scalars().first()
            if reader is None or reader.channel_id != ctx.channel.id:
                await ctx.error("そのidのRSSは登録されていません。")
                return
            await session.delete(reader)
            await session.commit()
        await ctx.success(f"ID: {rss_id} を削除しました。")


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(RSSCog(bot))
