from typing import Optional

import discord
from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs: dict) -> None:
        super(Context, self).__init__(**kwargs)

    async def error(self, content: str, description: Optional[str] = None) -> discord.Message:
        """
        エラー表示のための関数

        :param content: エラーのタイトル
        :param description: エラーの詳細
        :return: 送信したメッセージ
        """
        embed = discord.Embed(title=f"\U000026a0 {content}", color=0xffc107)
        if description is not None:
            embed.description = description

        return await self.send(embed=embed)

    async def success(self, content: str, description: Optional[str] = None) -> discord.Message:
        """
        コマンドの実行などに成功したときのための関数

        :param content: タイトル
        :param description: 内容
        :return: 送信したメッセージ
        """
        embed = discord.Embed(title=f"\U00002705 {content}", colour=discord.Colour.green())
        if description is not None:
            embed.description = description

        return await self.send(embed=embed)

    async def embed(self, embed: discord.Embed) -> discord.Message:
        """
        Embedのみを送信する関数

        :param embed: 送信するEmbed
        :return: 送信したメッセージ
        """
        return await self.send(embed=embed)
