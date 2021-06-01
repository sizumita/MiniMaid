from typing import TYPE_CHECKING

import discord
from discord.ext.ui import View, Component, Button, Message

from lib.context import Context
from view_models.audio_view_model import AudioViewModel

if TYPE_CHECKING:
    from cogs.audio import AudioBase
    from bot import MiniMaid


class AudioView(View):
    def __init__(self, bot: 'MiniMaid', cog: 'AudioBase', ctx: Context) -> None:
        super(AudioView, self).__init__(bot)
        self.viewModel = AudioViewModel(cog, ctx)

    async def body(self):
        if self.viewModel.disconnected:
            return Message(
                "切断しました。"
            )
        return Message(
            embed=discord.Embed(
                title="操作",
                description=f"音声タグ一覧と再生は`{self.viewModel.get_prefix()}audio tag`コマンドを実行してください。"
            ),
            component=Component(
                items=[
                    Button("切断")
                    .style(discord.ButtonStyle.danger)
                    .on_click(self.viewModel.disconnect)
                ]
            )
        )
