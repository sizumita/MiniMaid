from typing import TYPE_CHECKING
from datetime import datetime, timedelta
import asyncio
import aiohttp

import feedparser
import discord

from lib.database.query import select_all_feeds
from lib.database.models import Feed

if TYPE_CHECKING:
    from bot import MiniMaid

DIFF = timedelta(hours=9)


def strptime(text: str) -> datetime:
    dt = datetime.strptime(text, "%Y-%m-%dT%H:%M:%S%z")
    return dt.replace(tzinfo=None)


class FeedScheduler:
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot
        self.task = self.bot.loop.create_task(self.task())  # type: ignore

    async def send_entry(self, feed: Feed, embed: discord.Embed) -> None:
        try:
            for reader in feed.readers:
                channel = self.bot.get_channel(reader.channel_id)
                if channel is not None:
                    await channel.send(embed=embed)
        except Exception as e:
            print(e)

    async def send_new_entries(self, feed: Feed) -> None:
        async with aiohttp.ClientSession(loop=self.bot.loop) as http_session:
            async with http_session.get(feed.url) as response:
                if response.status >= 400:
                    feed.available = False
                    return
                raw_data = await response.text()
            data = feedparser.parse(raw_data)
            entries = [entry for entry in data.entries
                       if strptime(entry.updated).timestamp() >= feed.updated_at.timestamp()
                       ]
        for entry in sorted(entries, key=lambda x: strptime(x.updated)):
            description = entry.summary[:120]
            if description != entry.summary:
                description += "..."
            embed = discord.Embed(
                description=f"**[{entry.title}]({entry.link})**\n\n{description}",
                timestamp=strptime(entry.updated),
                colour=discord.Colour.orange()
            )
            embed.set_footer(text=entry.author)
            self.bot.loop.create_task(self.send_entry(feed, embed))

    async def fetch_all_feeds(self) -> None:
        now = datetime.utcnow()
        async with self.bot.db.Session() as session:
            result = await session.execute(select_all_feeds())
            feeds = result.scalars().all()
            for feed in feeds:
                await self.send_new_entries(feed)
                feed.updated_at = now
            await session.commit()

    async def task(self) -> None:
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.fetch_all_feeds()
            except Exception as e:
                print(e)

            await asyncio.sleep(10 * 60)
