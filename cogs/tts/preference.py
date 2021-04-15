from typing import TYPE_CHECKING
from collections import defaultdict
import asyncio
import json
import re

from discord.ext.commands import (
    Cog,
    group,
    guild_only,
)
import discord

from lib.context import Context
from lib.embed import user_voice_preference_embed
from lib.database.query import select_user_setting, select_guild_setting
from lib.database.models import UserVoicePreference, GuildVoicePreference

if TYPE_CHECKING:
    from bot import MiniMaid


class TTSPreferenceCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot

    async def update_user_preference(self, ctx: Context, speed=None, tone=None, intone=None, volume=None):
        async with self.bot.db.Session() as session:
            result = await session.execute(select_user_setting(ctx.author.id))
            pref: UserVoicePreference = result.scalars().first()
            if pref is None:
                new = UserVoicePreference(user_id=ctx.author.id)
                if speed is not None:
                    new.speed = speed
                if tone is not None:
                    new.tone = tone
                if intone is not None:
                    new.intone = intone
                if volume is not None:
                    new.volume = volume

                session.add(new)
                await session.commit()
                self.bot.dispatch("user_preference_update", new)
                return

            if speed is not None:
                pref.speed = speed
            if tone is not None:
                pref.tone = tone
            if intone is not None:
                pref.intone = intone
            if volume is not None:
                pref.volume = volume

            await session.commit()
            self.bot.dispatch("user_preference_update", pref)
        await ctx.success("設定しました。", f"`{ctx.prefix}pref`コマンドで確認できます。")

    @group(name="preference", aliases=["pref"], invoke_without_command=True)
    async def preference(self, ctx: Context):
        async with self.bot.db.Session() as session:
            result = await session.execute(select_user_setting(ctx.author.id))
            pref = result.scalars().first()
            if pref is None:
                pref = UserVoicePreference(user_id=ctx.author.id)
                session.add(pref)
            await session.commit()
        await ctx.embed(user_voice_preference_embed(ctx, pref))

    @preference.command(name="speed")
    async def tts_speed(self, ctx: Context, value: float):
        if not (0.5 <= value <= 2.0):
            await ctx.error("速さは0.5以上2.0以内で指定してください。")
            return
        await self.update_user_preference(ctx, speed=value)

    @preference.command(name="volume")
    async def tts_volume(self, ctx: Context, value: float):
        if not (-20.0 <= value <= 0.0):
            await ctx.error("速さは0.5以上2.0以内で指定してください。")
            return
        await self.update_user_preference(ctx, volume=value)

    @preference.command(name="tone")
    async def tts_tone(self, ctx: Context, value: float):
        if not (-20.0 <= value <= 20.0):
            await ctx.error("トーンは-20.0以上20.0以内で指定してください。")
            return
        await self.update_user_preference(ctx, tone=value)

    @preference.command(name="intone")
    async def tts_intone(self, ctx: Context, value: float):
        if not (0.0 <= value <= 4.0):
            await ctx.error("イントネーションは0.0以上4.0以内で指定してください。")
            return
        await self.update_user_preference(ctx, tone=value)

    @preference.command(name="reset")
    async def tts_reset(self, ctx: Context):
        await self.update_user_preference(ctx, volume=-6.0, speed=1.0, tone=0.0, intone=1.0)


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(TTSPreferenceCog(bot))
