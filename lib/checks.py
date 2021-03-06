from typing import Any

from discord.ext.commands import check
import discord

from lib.context import Context
from lib.errors import BotNotConnected, UserNotConnected, NoStageChannel


def bot_connected_only() -> Any:
    """
    BotがVCに接続しているかのチェック

    :return: check
    """
    def predicate(ctx: Context) -> bool:
        if ctx.voice_client is None:
            raise BotNotConnected()
        return True

    return check(predicate)


def user_connected_only() -> Any:
    """
    コマンドを打ったユーザーがVCに接続しているかのチェック

    :return: check
    """
    def predicate(ctx: Context) -> bool:
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            raise UserNotConnected()
        return True

    return check(predicate)


def voice_channel_only() -> Any:
    """
    ユーザーが接続しているチャンネルがVCであるかのチェック

    :return: check
    """
    def predicate(ctx: Context) -> bool:
        if isinstance(ctx.author.voice.channel, discord.StageChannel):
            raise NoStageChannel()
        return True

    return check(predicate)
