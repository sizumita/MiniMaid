from typing import TYPE_CHECKING

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


class TextToSpeechBase(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.reading_guilds = {}
        self.bot = bot


class TextToSpeechCommandMixin(TextToSpeechBase):
    @command()
    @voice_channel_only()
    @user_connected_only()
    @guild_only()
    async def join(self, ctx: Context) -> None:
        command()
        if ctx.guild.id in self.reading_guilds.keys():
            await ctx.error("すでに接続しています", f"`{ctx.prefix}move`コマンドを使用してください。")
            return

        channel = ctx.author.voice.channel

        await channel.connect(timeout=30.0)
        self.reading_guilds[ctx.guild.id] = (ctx.channel.id, channel.id)
        await ctx.success("接続しました。")

    @command()
    @bot_connected_only()
    @guild_only()
    async def leave(self, ctx: Context) -> None:
        # TODO: queueを消す
        await ctx.guild.voice_client.disconnect(force=True)
        del self.reading_guilds[ctx.guild.id]
        await ctx.success("切断しました。")

    @command()
    @voice_channel_only()
    @user_connected_only()
    @bot_connected_only()
    @guild_only()
    async def move(self, ctx: Context) -> None:
        # TODO queueを消す
        await ctx.voice_client.move_to(ctx.author.voice.channel)
        self.reading_guilds[ctx.guild.id] = (ctx.channel.id, ctx.author.voice.channel.id)
        await ctx.success("移動しました。")


class TextToSpeechCog(TextToSpeechCommandMixin):
    def __init__(self, bot: 'MiniMaid') -> None:
        super(TextToSpeechCog, self).__init__(bot)

    @Cog.listener(name="on_message")
    async def read_text(self, message: discord.Message) -> None:
        if message.guild is None:
            return
        if message.guild.id in self.reading_guilds.keys():
            pass


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(TextToSpeechCog(bot))
