from typing import TYPE_CHECKING, Any

from discord.ext.commands import (
    Cog,
    command,
    guild_only,
)
import discord

from lib.context import Context
from lib.checks import bot_connected_only, user_connected_only, voice_channel_only

if TYPE_CHECKING:
    from bot import MiniMaid


class TextToSpeechCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot
        self.reading_guilds = {}  # guild_id: (text_channel_id, voice_channel_id)

    @command()
    @guild_only()
    @user_connected_only()
    @voice_channel_only()
    async def join(self, ctx: Context) -> None:
        if ctx.guild.id in self.reading_guilds.keys():
            await ctx.error("すでに接続しています", f"`{ctx.prefix}move`コマンドを使用してください。")
            return

        channel = ctx.author.voice.channel

        await channel.connect(timeout=30.0)
        self.reading_guilds[ctx.guild.id] = (ctx.channel.id, channel.id)
        await ctx.success("接続しました。")

    @command()
    @guild_only()
    @bot_connected_only()
    async def leave(self, ctx: Context) -> None:
        # TODO: queueを消す
        await ctx.guild.voice_client.disconnect(force=True)
        await ctx.success("切断しました。")

    @command()
    @guild_only()
    @bot_connected_only()
    @user_connected_only()
    @voice_channel_only()
    async def move(self, ctx: Context) -> None:
        # TODO queueを消す
        await ctx.voice_client.move_to(ctx.author.voice.channel)
        self.reading_guilds[ctx.guild.id] = (ctx.channel.id, ctx.author.voice.channel.id)
        await ctx.success("移動しました。")


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(TextToSpeechCog(bot))
