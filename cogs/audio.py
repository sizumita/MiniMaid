from typing import TYPE_CHECKING, Optional, List, Dict
from collections import defaultdict
import asyncio
import re
from io import BytesIO
from uuid import uuid4
from datetime import datetime
import os

from discord.ext.commands import (
    Cog,
    MessageConverter,
    group,
    guild_only,
    cooldown,
    BucketType,
    command,
    is_owner
)
import discord
import aiohttp
from sqlalchemy.exc import IntegrityError

from lib.context import Context
from lib.checks import user_connected_only, bot_connected_only, voice_channel_only
from lib.audio import AudioEngine
from lib.database.models import AudioTag
from lib.database.query import select_audio_tag, select_audio_tags
from lib.discord.voice_client import MiniMaidVoiceClient

if TYPE_CHECKING:
    from bot import MiniMaid

url_compiled = re.compile(r"^https?://[\w!?/+\-_~=;.,*&@#$%()'\[\]]+$")
FILESIZE_LIMIT = 25 * 10 ** 6


class TagAttachment:
    def __init__(self, audio_tag: AudioTag):
        self.tag = audio_tag
        self.filetype = audio_tag.audio_url.split(".")[-1]
        self.filename = f"{self.tag.name}.{self.filetype}"
        self.url = self.tag.audio_url

    async def read(self) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.tag.audio_url) as response:
                return await response.read()


class AudioBase(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot
        self.connecting_guilds: List[int] = []
        self.locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.engine = AudioEngine(self.bot.loop)
        self.recording_guilds: List[int] = []
        self.invent_mode = False if os.environ.get("INVENT", "0") == "0" else True

    @command()
    @is_owner()
    async def invent_mode(self, ctx: Context) -> None:
        """invent modeを一時的に変更します。"""
        self.invent_mode = not self.invent_mode
        await ctx.success(f"invent modeを{self.invent_mode}に変更しました。")

    @Cog.listener(name="on_voice_state_update")
    async def check_all_member_left(self,
                                    member: discord.Member,
                                    before: discord.VoiceState,
                                    after: discord.VoiceState) -> None:
        if member.bot:
            return
        if member.guild.id not in self.connecting_guilds:
            return
        if before.channel is None:
            return
        me: discord.Member = member.guild.me
        if me.voice is None or me.voice.channel is None:
            return
        if not [m for m in me.voice.channel.members if not m.bot]:
            await me.guild.voice_client.disconnect(force=True)


class AudioCommandMixin(AudioBase):
    @group(name="audio", invoke_without_command=True)
    @user_connected_only()
    @guild_only()
    async def audio(self, ctx: Context) -> None:
        if ctx.guild.id in self.bot.get_cog("TextToSpeechCog").reading_guilds.keys():
            await ctx.error("読み上げ機能側で接続されています。", "切断してから再接続してください。")
            return
        if ctx.guild.id in self.connecting_guilds:
            await ctx.send("すでに接続しています。切断してから再接続します...")
            if ctx.guild.voice_client is not None:
                await ctx.guild.voice_client.disconnect(force=True)
                self.connecting_guilds.remove(ctx.guild.id)

        await ctx.author.voice.channel.connect(timeout=30.0, cls=MiniMaidVoiceClient)
        self.connecting_guilds.append(ctx.guild.id)
        await ctx.success("接続しました。")

    @audio.command(aliases=["dc", "leave"])
    @voice_channel_only()
    @bot_connected_only()
    @user_connected_only()
    @guild_only()
    async def disconnect(self, ctx: Context) -> None:
        if ctx.guild.id not in self.connecting_guilds:
            await ctx.error("オーディオプレーヤー側では接続されていません。")
            return

        ctx.voice_client.stop()
        await ctx.voice_client.disconnect(force=True)
        self.connecting_guilds.remove(ctx.guild.id)
        await ctx.success("切断しました。")

    @audio.command(name="file", aliases=["play"])
    @voice_channel_only()
    @bot_connected_only()
    @user_connected_only()
    @guild_only()
    @cooldown(1, 60, BucketType.guild)
    async def play_audio_file(self,
                              ctx: Context,
                              message: Optional[MessageConverter],
                              tag: Optional[str]) -> None:
        if ctx.guild.id not in self.connecting_guilds:
            await ctx.error("オーディオプレーヤー側では接続されていません。")
            return ctx.command.reset_cooldown(ctx)

        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if attachment.filename.endswith((".mp3", ".wav")):
                if attachment.size > FILESIZE_LIMIT:
                    await ctx.error("ファイルサイズがデカすぎます。25MB以内にしてください。")
                    return ctx.command.reset_cooldown(ctx)
                file = attachment
            else:
                await ctx.error("ファイルの拡張子はmp3かwavにしてください。")
                return ctx.command.reset_cooldown(ctx)
        elif message is not None:
            msg: discord.Message = message
            if msg.attachments:
                attachment = msg.attachments[0]
                if attachment.filename.endswith((".mp3", ".wav")):
                    if attachment.size > FILESIZE_LIMIT:
                        await ctx.error("ファイルサイズがデカすぎます。25MB以内にしてください。")
                        return ctx.command.reset_cooldown(ctx)
                    file = attachment
                else:
                    await ctx.error("ファイルの拡張子はmp3かwavにしてください。")
                    return ctx.command.reset_cooldown(ctx)
            else:
                await ctx.error("このメッセージにはファイルがついていません。")
                return ctx.command.reset_cooldown(ctx)
        elif tag is not None:
            async with self.bot.db.Session() as session:
                result = await session.execute(select_audio_tag(ctx.guild.id, tag))
                audio_tag = result.scalars().first()
                if audio_tag is None:
                    await ctx.error("その名前のタグは存在しませんでした。")
                    return ctx.command.reset_cooldown(ctx)
            file = TagAttachment(audio_tag)
        else:
            await ctx.error("ファイルを一緒に送信するかファイルがついているメッセージを引数に入れてください。")
            return ctx.command.reset_cooldown(ctx)

        source = await self.engine.create_source(file)
        async with self.locks[ctx.guild.id]:
            if ctx.guild.voice_client is None:
                return ctx.command.reset_cooldown(ctx)

            def check(ctx2: Context) -> bool:
                return ctx2.channel.id == ctx.channel.id
            await ctx.success(f"{file.filename}を再生します", f"[ファイルURL]({file.url})")

            event = asyncio.Event(loop=self.bot.loop)
            ctx.voice_client.play(source, after=lambda x: event.set())
            for coro in asyncio.as_completed([event.wait(), self.bot.wait_for("skip", check=check, timeout=None)]):
                result = await coro
                if isinstance(result, Context):
                    ctx.voice_client.stop()
                    await result.success("skipしました。")
                break
            await asyncio.sleep(5)
            ctx.command.reset_cooldown(ctx)

    @audio.group(name="tag", invoke_without_command=True)
    @guild_only()
    async def voice_tag(self, ctx: Context) -> None:
        async with self.bot.db.SerializedSession() as session:
            result = await session.execute(select_audio_tags(ctx.guild.id))
            tags = result.scalars().all()
        if not tags:
            await ctx.error("タグは一つも作成されていません。")
            return
        embed = discord.Embed(title="タグ一覧", description="\n".join([tag.name for tag in tags]))
        await ctx.embed(embed)

    @voice_tag.command(name="add")
    @cooldown(10, 60.0, BucketType.guild)
    async def voice_tag_add(self, ctx: Context, name: str, msg: Optional[MessageConverter], url: Optional[str]) -> None:
        """AudioTagを生成する"""

        # タグ用のaudio url生成
        if msg is not None:
            message: discord.Message = msg
            if message.attachments:
                attachment = message.attachments[0]
                if attachment.filename.endswith((".mp3", ".wav")):
                    if attachment.size > FILESIZE_LIMIT:
                        await ctx.error("ファイルサイズがデカすぎます。25MB以内にしてください。")
                        return
                    audio_url = attachment.url
                else:
                    await ctx.error("ファイルの拡張子はmp3かwavにしてください。")
                    ctx.command.reset_cooldown(ctx)
                    return
            else:
                await ctx.error("このメッセージにはファイルがついていません。")
                return

        elif ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if attachment.filename.endswith((".mp3", ".wav")):
                if attachment.size > FILESIZE_LIMIT:
                    await ctx.error("ファイルサイズがデカすぎます。25MB以内にしてください。")
                    return
                audio_url = attachment.url
            else:
                await ctx.error("ファイルの拡張子はmp3かwavにしてください。")
                ctx.command.reset_cooldown(ctx)
                return

        elif url is not None and url_compiled.match(url):
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(url) as response:
                    if not (200 <= response.status <= 299):
                        await ctx.error("URLからファイルの取得に失敗しました。")
                        return
                    data = await response.read()
                    if len(data) > FILESIZE_LIMIT:
                        await ctx.error("ファイルサイズがデカすぎます。25MB以内にしてください。")
                        return
                    message = await ctx.send(file=discord.File(
                        BytesIO(data),
                        filename=f"{uuid4()}.{url.split('.')[-1]}"
                    ))
                    audio_url = message.attachments[0].url
        else:
            await ctx.error("ファイルを一緒に送信するかファイルがついているメッセージか音楽のURLを引数に入れてください。")
            return

        # タグの作成
        async with self.bot.db.SerializedSession() as session:
            try:
                async with session.begin():
                    tag = AudioTag(
                        guild_id=ctx.guild.id,
                        name=name,
                        audio_url=audio_url,
                        owner_id=ctx.author.id
                    )
                    session.add(tag)
                    text = f"タグ: `{name}`を追加しました。"
            except IntegrityError:
                async with session.begin():
                    result = await session.execute(select_audio_tag(ctx.guild.id, name))
                    old_tag = result.scalars().first()
                    old_tag.audio_url = audio_url
                text = f"タグ: `{name}`を更新しました。"
        await ctx.success(text)

    @voice_tag.command(name="remove", aliases=["delete", "rm"])
    async def voice_tag_delete(self, ctx: Context, name: str) -> None:
        async with self.bot.db.SerializedSession() as session:
            result = await session.execute(select_audio_tag(ctx.guild.id, name))
            tag = result.scalars().first()
            if tag is None:
                await ctx.error("その名前のタグは存在していません。")
                return
            await session.delete(tag)
            await session.commit()
        await ctx.success(f"タグ: {name}の削除に成功しました。")

    @audio.command(name="replay", aliases=["clip"])
    @voice_channel_only()
    @bot_connected_only()
    @user_connected_only()
    @guild_only()
    @cooldown(1, 35, BucketType.guild)
    async def replay_audio(self, ctx: Context) -> None:
        if ctx.guild.id not in self.connecting_guilds:
            await ctx.error("オーディオプレーヤー側では接続されていません。")
            ctx.command.reset_cooldown(ctx)
            return
        if ctx.guild.id in self.recording_guilds:
            await ctx.error("すでに録音を開始しています。")
            return
        self.recording_guilds.append(ctx.guild.id)
        try:
            await ctx.success("30秒前からのクリップを作成します...")
            file = await ctx.voice_client.replay()
            if file is None:
                await ctx.error("エラーが発生しました。もしエラーが再発するようであれば再接続してください。")
                return
            timestamp = datetime.utcnow().timestamp()
            file.seek(0)
            await ctx.send("作成終了しました。", file=discord.File(file, f"{timestamp}.wav"))
        except Exception as e:
            await ctx.error("エラーが発生しました。")
            raise e
        finally:
            self.recording_guilds.remove(ctx.guild.id)

    @group(name="record", invoke_without_command=True)
    @guild_only()
    async def voice_recorder(self, ctx: Context) -> None:
        embed = discord.Embed(title="オーディオレコーダーの使い方", colour=discord.Colour.gold())
        embed.add_field(
            name="録音の仕方",
            value=f"**{ctx.prefix}record start**で録音を開始します。最大30秒まで録音できます。",
            inline=False
        )
        embed.add_field(
            name="録音の終了の仕方",
            value=f"録音を途中でやめたい場合は、**{ctx.prefix}record stop**でやめることができます。",
            inline=False
        )
        embed.add_field(
            name="録音されたファイルについて",
            value="録音されたファイルはBotでは保存せずチャンネルにwavファイルとして投稿されます。",
            inline=False
        )
        await ctx.embed(embed)

    @voice_recorder.command(name="start")
    @voice_channel_only()
    @bot_connected_only()
    @user_connected_only()
    @cooldown(1, 86400, BucketType.guild)
    async def record_start(self, ctx: Context) -> None:
        if ctx.guild.id not in self.connecting_guilds:
            await ctx.error("オーディオプレーヤー側では接続されていません。")
            ctx.command.reset_cooldown(ctx)
            return
        if ctx.guild.id in self.recording_guilds:
            await ctx.error("すでに録音を開始しています。")
            ctx.command.reset_cooldown(ctx)
            return

        self.recording_guilds.append(ctx.guild.id)
        try:
            await ctx.success("録音開始します...")
            file = await ctx.voice_client.record(self.invent_mode)
            if file is None:
                await ctx.error("エラーが発生しました。もしエラーが再発するようであれば再接続してください。")
                return
            await ctx.success("録音終了しました。")
            timestamp = datetime.utcnow().timestamp()
            file.seek(0)
            await ctx.send(file=discord.File(file, f"{timestamp}.mp3"))
        except Exception as e:
            await ctx.error("エラーが発生しました。")
            raise e
        finally:
            self.recording_guilds.remove(ctx.guild.id)
            await asyncio.sleep(10)
            ctx.command.reset_cooldown(ctx)

    @voice_recorder.command(name="stop", aliases=["end"])
    @voice_channel_only()
    @bot_connected_only()
    @user_connected_only()
    async def record_stop(self, ctx: Context) -> None:
        if ctx.guild.id not in self.connecting_guilds:
            await ctx.error("オーディオプレーヤー側では接続されていません。")
            return
        self.bot.dispatch("record_stop")


class AudioCog(AudioCommandMixin):
    pass


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(AudioCog(bot))
