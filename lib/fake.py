"""
テスト用のFakeクラス
"""
from typing import Optional, Any

import discord
from discord.ext import commands


class FakeEmoji(discord.Emoji):
    def __init__(self, _id: int) -> None:
        self.id = _id
        discord.Message._state

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, FakeEmoji):
            return other.id == self.id
        return False


class FakeBot(commands.Bot):
    def __init__(self) -> None:
        super(FakeBot, self).__init__("")

    def get_emoji(self, id: int) -> Optional[FakeEmoji]:
        if id == 1:
            return FakeEmoji(id)
        return None
