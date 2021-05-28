from typing import TYPE_CHECKING

import discord
from discord.ext.ui import View, Component, Button

from lib.context import Context
from view_models.audio_tag import AudioTagViewModel

if TYPE_CHECKING:
    from cogs.audio import AudioBase


EMOJIS = [
    "\N{DIGIT ONE}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}",
    "\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}",
]


class AudioTagView(View):
    def __init__(self, cog: 'AudioBase', ctx: Context, tags: list) -> None:
        super(AudioTagView, self).__init__()
        self.viewModel = AudioTagViewModel(self.bot, cog, ctx, tags)

    async def start(self, bot, channel):
        self.viewModel.bot = bot
        await super(AudioTagView, self).start(bot, channel)

    def make_embed(self):
        embed = discord.Embed(title="タグ一覧", colour=discord.Colour.blurple())
        for i, x in enumerate(self.viewModel.get_tags()):
            embed.add_field(name=EMOJIS[i], value=x.name, inline=False)
        return embed

    def play_callback(self, index: int) -> callable:
        async def func(interaction: discord.Interaction) -> None:
            await self.viewModel.play(interaction, index)
        return func

    async def play_buttons(self):
        buttons = []
        m = len(self.viewModel.get_tags())
        for i, e in enumerate(EMOJIS):
            buttons.append(
                Button("再生").emoji(e)
                .disabled(self.viewModel.is_playing or i >= m or self.viewModel.is_closed)
                .style(discord.ButtonStyle.success)
                .on_click(self.play_callback(i))
            )
        return buttons

    async def body(self):
        return Component(
            embed=self.make_embed(),
            buttons=[
                await self.play_buttons(),
                [
                    Button("前ページ")
                    .style(discord.ButtonStyle.grey)
                    .disabled(self.viewModel.page == 0)
                    .on_click(self.viewModel.priv_page),
                    Button("次ページ")
                    .style(discord.ButtonStyle.grey)
                    .disabled(self.viewModel.page == self.viewModel.max_page)
                    .on_click(self.viewModel.next_page)
                ],
                [
                    Button("スキップ")
                    .style(discord.ButtonStyle.red)
                    .disabled(not self.viewModel.is_playing)
                    .on_click(self.viewModel.skip)
                ]
            ]
        )
