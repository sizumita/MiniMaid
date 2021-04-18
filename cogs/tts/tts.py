from typing import TYPE_CHECKING, List, Dict, Tuple
from collections import defaultdict
import asyncio
import json
import re

from discord.ext.commands import (
    Cog,
    command,
    guild_only,
)
import discord

from lib.context import Context
from lib.database.query import select_user_setting, select_guild_setting, select_voice_dictionaries
from lib.database.models import UserVoicePreference, GuildVoicePreference, VoiceDictionary
from lib.checks import bot_connected_only, user_connected_only, voice_channel_only
from lib.tts import TextToSpeechEngine

if TYPE_CHECKING:
    from bot import MiniMaid


comment_compiled = re.compile(r"//.*[^\n]\n")


class TextToSpeechBase(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.reading_guilds: Dict[int, Tuple[int, int]] = {}
        self.bot = bot
        self.locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.joined_members: Dict[int, List[discord.Member]] = defaultdict(list)
        self.left_members: Dict[int, List[discord.Member]] = defaultdict(list)
        self.voice_event_locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)  # ユーザーが入退室した際の読み上げを割り込ませるlock
        self.users: Dict[int, UserVoicePreference] = {}
        self.engines: Dict[int, TextToSpeechEngine] = {}
        self.english_dict: Dict[str, str] = {}
        with open("dic.json", "r") as f:
            t = f.read()
            self.english_dict = json.loads(re.sub(comment_compiled, "", t))


class TextToSpeechCommandMixin(TextToSpeechBase):
    @command()
    @voice_channel_only()
    @user_connected_only()
    @guild_only()
    async def join(self, ctx: Context) -> None:
        if ctx.guild.id in self.reading_guilds.keys():
            await ctx.error("すでに接続しています", f"`{ctx.prefix}move`コマンドを使用してください。")
            return
        if ctx.guild.id in self.bot.get_cog("AudioCog").connecting_guilds:
            await ctx.error("オーディオプレーヤー側で接続しています。切断してから再接続してください。")
            return

        channel = ctx.author.voice.channel

        await channel.connect(timeout=30.0)
        self.reading_guilds[ctx.guild.id] = (ctx.channel.id, channel.id)
        await ctx.success("接続しました。")

    @command()
    @bot_connected_only()
    @guild_only()
    async def leave(self, ctx: Context) -> None:
        if ctx.guild.id not in self.reading_guilds.keys():
            await ctx.error("読み上げ側では接続されていません。")
            return
        del self.reading_guilds[ctx.guild.id]
        await ctx.guild.voice_client.disconnect(force=True)
        async with self.locks[ctx.guild.id]:
            del self.engines[ctx.guild.id]
        await ctx.success("切断しました。")

    @command()
    @voice_channel_only()
    @user_connected_only()
    @bot_connected_only()
    @guild_only()
    async def move(self, ctx: Context) -> None:
        if ctx.guild.id not in self.reading_guilds.keys():
            await ctx.error("読み上げ側では接続されていません。")
            return
        del self.reading_guilds[ctx.guild.id]
        await ctx.voice_client.disconnect(force=True)
        await ctx.author.voice.channel.connect(timeout=30.0)
        self.reading_guilds[ctx.guild.id] = (ctx.channel.id, ctx.author.voice.channel.id)
        await ctx.success("移動しました。")

    @command()
    async def skip(self, ctx: Context) -> None:
        self.bot.dispatch("skip", ctx)


class TextToSpeechEventMixin(TextToSpeechBase):
    async def read_users_with_lock(self, message: discord.Message) -> None:
        engine = await self.get_engine(message.guild.id)
        text = ""
        async with self.voice_event_locks[message.guild.id]:
            if self.left_members[message.guild.id]:
                if len(self.left_members[message.guild.id]) > 5:
                    text += f"{len(self.left_members[message.guild.id])}人"
                elif engine.guild_preference.read_nick:
                    text += "、".join(f"{member.display_name}さん" for member in self.left_members[message.guild.id])
                else:
                    text += "、".join(f"{member.name}さん" for member in self.left_members[message.guild.id])
                text += "が退室しました。"
                self.left_members[message.guild.id].clear()

            if self.joined_members[message.guild.id]:
                if len(self.joined_members[message.guild.id]) > 5:
                    text += f"{len(self.joined_members[message.guild.id])}人"
                elif engine.guild_preference.read_nick:
                    text += "、".join(f"{member.display_name}さん" for member in self.joined_members[message.guild.id])
                else:
                    text += "、".join(f"{member.name}さん" for member in self.joined_members[message.guild.id])
                text += "が入室しました。"
                self.joined_members[message.guild.id].clear()
            if not text:
                return
            source = await engine.generate_default_source(text)
            event = asyncio.Event(loop=self.bot.loop)

            voice_client: discord.VoiceClient = message.guild.voice_client
            if voice_client is None:
                return

            voice_client.play(source, after=lambda err: event.set())
            await event.wait()

    async def queue_text_to_speech(self, message: discord.Message) -> None:
        user_preference = await self.get_user_preference(message.author.id)
        engine = await self.get_engine(message.guild.id)
        if message.author.bot and not engine.guild_preference.read_bot:
            return
        source = await engine.generate_source(message, user_preference, self.english_dict)
        if source is None:
            return

        async with self.locks[message.guild.id]:
            voice_client: discord.VoiceClient = message.guild.voice_client
            if voice_client is None:
                return
            await self.read_users_with_lock(message)

            def check(ctx: Context) -> bool:
                return ctx.channel.id == message.channel.id

            event = asyncio.Event(loop=self.bot.loop)
            voice_client.play(source, after=lambda err: event.set())
            for coro in asyncio.as_completed([event.wait(), self.bot.wait_for("skip", check=check, timeout=None)]):
                result = await coro
                if isinstance(result, Context):
                    voice_client.stop()
                    await result.success("skipしました。")
                break

    async def get_engine(self, guild_id: int) -> TextToSpeechEngine:
        if guild_id in self.engines.keys():
            return self.engines[guild_id]
        async with self.bot.db.Session() as session:
            async with session.begin():
                result = await session.execute(select_guild_setting(guild_id))
                pref = result.scalars().first()
                if pref is not None:
                    e = TextToSpeechEngine(self.bot.loop, pref, await self.get_dictionaries(guild_id))
                    self.engines[guild_id] = e
                    return e
                new = GuildVoicePreference(guild_id=guild_id)
                session.add(new)
        e = TextToSpeechEngine(self.bot.loop, new, await self.get_dictionaries(guild_id))
        self.engines[guild_id] = e
        return e

    async def get_dictionaries(self, guild_id: int) -> List[VoiceDictionary]:
        async with self.bot.db.Session() as session:
            async with session.begin():
                result = await session.execute(select_voice_dictionaries(guild_id))
                return result.scalars().all()

    async def get_user_preference(self, user_id: int) -> UserVoicePreference:
        if user_id in self.users.keys():
            return self.users[user_id]

        async with self.bot.db.Session() as session:
            async with session.begin():
                result = await session.execute(select_user_setting(user_id))
                pref = result.scalars().first()
                if pref is not None:
                    self.users[user_id] = pref
                    return pref
                new = UserVoicePreference(user_id=user_id)
                session.add(new)
        self.users[user_id] = new
        return new

    @Cog.listener(name="on_message")
    async def read_text(self, message: discord.Message) -> None:
        if message.content is None:
            return
        if message.guild is None:
            return
        if message.guild.id not in self.reading_guilds.keys():
            return
        context = await self.bot.get_context(message, cls=Context)
        if context.command is not None:
            return

        text_channel_id, voice_channel_id = self.reading_guilds[message.guild.id]
        if message.channel.id != text_channel_id:
            return

        await self.queue_text_to_speech(message)

    @Cog.listener(name="on_user_preference_update")
    async def on_user_preference_update(self, preference: UserVoicePreference) -> None:
        self.users[preference.user_id] = preference

    @Cog.listener(name="on_guild_preference_update")
    async def on_guild_preference_update(self, preference: GuildVoicePreference) -> None:
        if preference.guild_id in self.engines.keys():
            self.engines[preference.guild_id].update_guild_preference(preference)

    @Cog.listener(name="on_voice_dictionary_add")
    async def dictionary_add(self, guild: discord.Guild, dic: VoiceDictionary) -> None:
        if guild.id in self.engines.keys():
            self.engines[guild.id].update_dictionary("add", dic)

    @Cog.listener(name="on_voice_dictionary_update")
    async def dictionary_update(self, guild: discord.Guild, dic: VoiceDictionary) -> None:
        if guild.id in self.engines.keys():
            self.engines[guild.id].update_dictionary("update", dic)

    @Cog.listener(name="on_voice_dictionary_remove")
    async def dictionary_remove(self, guild: discord.Guild, dic: VoiceDictionary) -> None:
        if guild.id in self.engines.keys():
            self.engines[guild.id].update_dictionary("remove", dic)

    @Cog.listener(name="on_voice_state_update")
    async def check_bot_left(self,
                             member: discord.Member,
                             before: discord.VoiceState,
                             after: discord.VoiceState) -> None:
        if member.id != self.bot.user.id:
            return
        if member.guild.id not in self.reading_guilds.keys():
            return
        text_channel_id, voice_channel_id = self.reading_guilds[member.guild.id]
        if before.channel is None:
            return
        if before.channel.id == voice_channel_id and after.channel is None:
            # 切断
            if member.guild.id in self.reading_guilds.keys():
                del self.reading_guilds[member.guild.id]
            if member.guild.id in self.engines.keys():
                del self.engines[member.guild.id]

    @Cog.listener(name="on_voice_state_update")
    async def check_all_member_left(self,
                                    member: discord.Member,
                                    before: discord.VoiceState,
                                    after: discord.VoiceState) -> None:
        if member.bot:
            return
        if member.guild.id not in self.reading_guilds.keys():
            return
        if before.channel is None:
            return
        text_channel_id, voice_channel_id = self.reading_guilds[member.guild.id]

        if before.channel.id == voice_channel_id and after.channel is None:
            vc = member.guild.get_channel(voice_channel_id)
            if not [i for i in vc.members if not i.bot]:
                await member.guild.voice_client.disconnect(force=True)
                text_channel = self.bot.get_channel(text_channel_id)
                if text_channel is not None:
                    embed = discord.Embed(title="\U00002705 自動切断しました。", colour=discord.Colour.green())
                    await text_channel.send(embed=embed)
                if member.guild.id in self.reading_guilds.keys():
                    del self.reading_guilds[member.guild.id]
                if member.guild.id in self.engines.keys():
                    del self.engines[member.guild.id]

    @Cog.listener(name="on_voice_state_update")
    async def check_user_movement(self,
                                  member: discord.Member,
                                  before: discord.VoiceState,
                                  after: discord.VoiceState) -> None:
        if member.id == self.bot.user.id:
            return
        if member.bot:
            return
        if member.guild.id not in self.reading_guilds.keys():
            return
        text_channel_id, voice_channel_id = self.reading_guilds[member.guild.id]
        if after.channel is None:
            if before.channel is None:
                return
            if before.channel.id == voice_channel_id:
                if member.guild.id in self.engines.keys():
                    engine = await self.get_engine(member.guild.id)
                    if engine.guild_preference.read_leave:
                        self.left_members[member.guild.id].append(member)
        else:
            # 入室
            if before.channel is not None:
                return
            if after.channel.id == voice_channel_id:
                if member.guild.id in self.engines.keys():
                    engine = await self.get_engine(member.guild.id)
                    if engine.guild_preference.read_join:
                        self.joined_members[member.guild.id].append(member)


class TextToSpeechCog(TextToSpeechCommandMixin, TextToSpeechEventMixin):
    def __init__(self, bot: 'MiniMaid') -> None:
        super(TextToSpeechCog, self).__init__(bot)


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(TextToSpeechCog(bot))
