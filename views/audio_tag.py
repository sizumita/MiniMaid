from typing import TYPE_CHECKING

import discord
from discord.ext.ui import View, Component, Button, Message

from lib.context import Context
from view_models.audio_tag import AudioTagViewModel

if TYPE_CHECKING:
    from cogs.audio import AudioBase

EMOJIS = [
    "\U0001f1e6",
    "\U0001f1e7",
    "\U0001f1e8",
    "\U0001f1e9",
    "\U0001f1ea",
    "\U0001f1eb",
    "\U0001f1ec",
    "\U0001f1ed",
    "\U0001f1ee",
    "\U0001f1ef",
    "\U0001f1f0",
    "\U0001f1f1",
    "\U0001f1f2",
    "\U0001f1f3",
    "\U0001f1f4",
    "\U0001f1f5",
    "\U0001f1f6",
    "\U0001f1f7",
    "\U0001f1f8",
    "\U0001f1f9",
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
        text = ""
        for i, x in enumerate(self.viewModel.get_tags()):
            text += f"{EMOJIS[i]} {x.name}\n"
        embed.description = text[:2000]
        return embed

    def play_callback(self, index: int) -> callable:
        async def func(interaction: discord.Interaction) -> None:
            await self.viewModel.play(interaction, index)
        return func

    def play_buttons(self, r: range):
        buttons = []
        for x in r:
            buttons.append(
                Button("")
                .emoji(EMOJIS[x])
                .disabled(self.viewModel.is_playing or x >= len(self.viewModel.get_tags()))
                .on_click(self.play_callback(x))
                .style(discord.ButtonStyle.grey)
            )
        return buttons

    def select_buttons(self):
        return [
            Button("前ページ")
            .disabled(self.viewModel.page == 0)
            .on_click(self.viewModel.priv_page),
            Button("次ページ")
            .disabled(self.viewModel.page == self.viewModel.max_page)
            .on_click(self.viewModel.next_page),
            Button("スキップ")
            .style(discord.ButtonStyle.red)
            .on_click(self.viewModel.skip),
        ]

    async def body(self):
        return Message(
            embed=self.make_embed(),
            component=Component(
                items=[
                    self.select_buttons(),
                    self.play_buttons(range(0, 5)) if self.viewModel.can_play() else [],
                    self.play_buttons(range(5, 10)) if self.viewModel.can_play() else [],
                    self.play_buttons(range(10, 15)) if self.viewModel.can_play() else [],
                    self.play_buttons(range(15, 20)) if self.viewModel.can_play() else [],
                ]
            )
        )
