from typing import TYPE_CHECKING

import discord
from discord import ButtonStyle
from discord.ext.ui import View, Component, Button, Message

from lib.context import Context
from view_models.recorder import RecorderViewModel

if TYPE_CHECKING:
    from bot import MiniMaid


class RecorderView(View):
    def __init__(self, bot: 'MiniMaid', ctx: Context):
        super(RecorderView, self).__init__(bot)
        self.viewModel = RecorderViewModel(bot, ctx)

    def embed(self):
        embed = discord.Embed(colour=discord.Colour.blurple())
        if self.viewModel.status == 0:
            embed.title = "録音を開始します..."
        elif self.viewModel.status == -1:
            embed = discord.Embed(title=f"\U000026a0 ボイスチャンネルに接続していません。", color=0xffc107)
        elif self.viewModel.status == -2:
            embed = discord.Embed(title=f"\U000026a0 すでに録音を開始しています。", color=0xffc107)
        elif self.viewModel.status == 1:
            embed.title = "録音しています..."
            embed.description = f"録音を停止したい場合は`{self.viewModel.get_prefix()}record stop`と実行するか、ボタンを押してください。"
        elif self.viewModel.status == 2:
            embed.title = "録音終了しました"
        elif self.viewModel.status == -2:
            embed = discord.Embed(title=f"\U000026a0 エラーが発生しました。", color=0xffc107)
            embed.description = self.viewModel.error

        return embed

    def buttons(self):
        return [
            Button("ストップ")
                .style(ButtonStyle.blurple)
                .disabled(self.viewModel.status != 1)
                .on_click(self.viewModel.record_stop)
        ]

    async def body(self) -> Message:
        if self.viewModel.status in [-1, -2]:
            return Message(
                embed=self.embed()
            )

        message = Message(
            embed=self.embed(),
            component=Component(
                items=self.buttons()
            )
        ).on_appear(self.viewModel.record_start)

        return message
