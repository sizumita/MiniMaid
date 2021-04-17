from typing import TYPE_CHECKING, Optional, List, Dict
from collections import defaultdict
import asyncio

from discord.ext.commands import (
    Cog,
    MessageConverter,
    group,
    guild_only,
    cooldown,
    BucketType
)
import discord

from lib.context import Context
from lib.checks import user_connected_only, bot_connected_only, voice_channel_only
from lib.audio import AudioEngine

if TYPE_CHECKING:
    from bot import MiniMaid


class AudioCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot
        self.connecting_guilds: List[int] = []
        self.locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.engine = AudioEngine(self.bot.loop)

    @group(name="audio", invoke_without_command=True)
    @user_connected_only()
    @guild_only()
    async def audio(self, ctx: Context) -> None:
        if ctx.guild.id in self.bot.get_cog("TextToSpeechCog").reading_guilds.keys():
            await ctx.error("読み上げ機能側で接続されています。", "切断してから再接続してください。")
            return
        if ctx.guild.id in self.connecting_guilds:
            await ctx.error("すでに接続しています。", "切断してから再接続してください。")
            return

        await ctx.author.voice.channel.connect(timeout=30.0)
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

    @audio.command(name="file")
    @voice_channel_only()
    @bot_connected_only()
    @user_connected_only()
    @guild_only()
    @cooldown(1, 60, BucketType.guild)
    async def play_audio_file(self, ctx: Context, message: Optional[MessageConverter]) -> None:
        if ctx.guild.id not in self.connecting_guilds:
            await ctx.error("オーディオプレーヤー側では接続されていません。")
            ctx.command.reset_cooldown(ctx)
            return

        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if attachment.filename.endswith((".mp3", ".wav")):
                file = attachment
            else:
                await ctx.error("ファイルの拡張子はmp3かwavにしてください。")
                ctx.command.reset_cooldown(ctx)
                return
        elif message is not None:
            msg: discord.Message = message
            if msg.attachments:
                attachment = msg.attachments[0]
                if attachment.filename.endswith((".mp3", ".wav")):
                    file = attachment
                else:
                    await ctx.error("ファイルの拡張子はmp3かwavにしてください。")
                    ctx.command.reset_cooldown(ctx)
                    return
            else:
                await ctx.error("このメッセージにはファイルがついていません。")
                ctx.command.reset_cooldown(ctx)
                return
        else:
            await ctx.error("ファイルを一緒に送信するかファイルがついているメッセージを引数に入れてください。")
            ctx.command.reset_cooldown(ctx)
            return
        source = await self.engine.create_source(file)
        async with self.locks[ctx.guild.id]:
            if ctx.guild.voice_client is None:
                return

            def check(ctx2: Context) -> bool:
                return ctx2.channel.id == ctx.channel.id
            await ctx.success(f"{file.filename}を再生します", f"[ファイルURL]({attachment.url})")

            event = asyncio.Event(loop=self.bot.loop)
            ctx.voice_client.play(source, after=lambda x: event.set())
            for coro in asyncio.as_completed([event.wait(), self.bot.wait_for("skip", check=check, timeout=None)]):
                result = await coro
                if isinstance(result, Context):
                    ctx.voice_client.stop()
                    await result.success("skipしました。")
                break


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(AudioCog(bot))
