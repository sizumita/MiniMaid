from typing import TYPE_CHECKING
import re
import io

from discord.ext.commands import (
    Cog,
    group
)
import aiohttp
import feedparser

from lib.rss.scheduler import FeedScheduler
from lib.context import Context
from lib.database.models import Feed, Reader
from lib.database.query import select_feed, select_reader

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
        pass

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

    @rss.command()
    async def remove_rss(self, ctx: Context, rss_id: int) -> None:
        pass


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(RSSCog(bot))
