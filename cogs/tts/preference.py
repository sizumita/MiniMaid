from typing import TYPE_CHECKING

from discord.ext.commands import (
    Cog,
    group,
    guild_only,
    cooldown,
    BucketType
)

from lib.context import Context
from lib.embed import user_voice_preference_embed, guild_voice_preference_embed, voice_dictionaries_embed
from lib.database.query import (
    select_user_setting,
    select_guild_setting,
    select_voice_dictionaries,
    select_voice_dictionary
)
from lib.database.models import UserVoicePreference, GuildVoicePreference, VoiceDictionary

if TYPE_CHECKING:
    from bot import MiniMaid


class TTSPreferenceBase:
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot


class UserPreferenceMixin(TTSPreferenceBase):
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
                await ctx.success("設定しました。", f"`{ctx.prefix}pref`コマンドで確認できます。")
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


class GuildPreferenceMixin(TTSPreferenceBase):
    async def update_guild_preference(self, ctx: Context, change_field: str):
        async with self.bot.db.Session() as session:
            result = await session.execute(select_guild_setting(ctx.guild.id))
            pref = result.scalars().first()
            if pref is None:
                new = GuildVoicePreference(guild_id=ctx.guild.id)
                if change_field == "bot":
                    new.read_bot = not False
                elif change_field == "join":
                    new.read_join = not False
                elif change_field == "leave":
                    new.read_leave = not False
                elif change_field == "name":
                    new.read_name = not True
                elif change_field == "nick":
                    new.read_nick = not True
                session.add(new)
                await session.commit()
                self.bot.dispatch("guild_preference_update", new)
                await ctx.success("設定しました。", f"`{ctx.prefix}gpref`コマンドで確認できます。")
                return new

            if change_field == "bot":
                pref.read_bot = not pref.read_bot
            elif change_field == "join":
                pref.read_join = not pref.read_join
            elif change_field == "leave":
                pref.read_leave = not pref.read_leave
            elif change_field == "name":
                pref.read_name = not pref.read_name
            elif change_field == "nick":
                pref.read_nick = not pref.read_nick

            await session.commit()
            self.bot.dispatch("guild_preference_update", pref)
            await ctx.success("設定しました。", f"`{ctx.prefix}gpref`コマンドで確認できます。")

    @group(name="gpreference", aliases=["gpref"], invoke_without_command=True)
    @guild_only()
    async def guild_preference(self, ctx: Context):
        async with self.bot.db.Session() as session:
            result = await session.execute(select_guild_setting(ctx.guild.id))
            pref = result.scalars().first()
            if pref is None:
                pref = GuildVoicePreference(guild_id=ctx.guild.id)
                session.add(pref)
            await session.commit()
        await ctx.embed(guild_voice_preference_embed(ctx, pref))

    @guild_preference.command(name="bot")
    async def speak_bot(self, ctx: Context):
        await self.update_guild_preference(ctx, "bot")

    @guild_preference.command(name="join")
    async def speak_join(self, ctx: Context):
        await self.update_guild_preference(ctx, "join")

    @guild_preference.command(name="leave")
    async def speak_leave(self, ctx: Context):
        await self.update_guild_preference(ctx, "leave")

    @guild_preference.command(name="nick")
    async def speak_nick(self, ctx: Context):
        await self.update_guild_preference(ctx, "nick")

    @guild_preference.command(name="name")
    async def speak_name(self, ctx: Context):
        await self.update_guild_preference(ctx, "name")


class VoiceDictionaryMixin(TTSPreferenceBase):
    @group(name="dictionary", aliases=["dic", "dict"], invoke_without_command=True)
    @guild_only()
    async def voice_dictionary(self, ctx: Context):
        async with self.bot.db.Session() as session:
            result = await session.execute(select_voice_dictionaries(ctx.guild.id))
            dictionaries = result.scalars().all()
            await session.commit()
        await ctx.embed(voice_dictionaries_embed(ctx, dictionaries))

    @voice_dictionary.command(name="add", alases=["set", "new"])
    @cooldown(5, 60.0, type=BucketType.guild)
    async def add_voice_dictionary(self, ctx: Context, before: str, after: str):
        async with self.bot.db.Session() as session:
            result = await session.execute(select_voice_dictionary(ctx.guild.id, before))
            dic = result.scalars().first()
            if dic is None:
                new = VoiceDictionary(guild_id=ctx.guild.id, before=before, after=after)
                session.add()
                await session.commit()
                await ctx.success(f"`{before}`を`{after}`として登録しました。")
                self.bot.dispatch("voice_dictionary_add", ctx.guild, new)
                return
            old = str(dic.after)
            dic.after = after
            await session.commit()
            await ctx.success(f"`{before}`を`{after}`として更新しました。(元: `{old}`)")
            self.bot.dispatch("voice_dictionary_update", ctx.guild, dic)

    @voice_dictionary.command(name="remove", aliases=["del", "delete"])
    async def remove_voice_dictionary(self, ctx: Context, before: str):
        async with self.bot.db.Session() as session:
            result = await session.execute(select_voice_dictionary(ctx.guild.id, before))
            dic = result.scalars().first()
            if dic is None:
                await ctx.error(f"`{before}`は登録されていません。")
                return
            await session.delete(dic)
            await session.commit()
            await ctx.success(f"`{before}`を削除しました。")
            self.bot.dispatch("voice_dictionary_remove", ctx.guild, dic)


class TTSPreferenceCog(Cog, UserPreferenceMixin, GuildPreferenceMixin, VoiceDictionaryMixin):
    pass


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(TTSPreferenceCog(bot))
