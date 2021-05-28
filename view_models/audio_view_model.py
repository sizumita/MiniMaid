from typing import TYPE_CHECKING

import discord
from discord.ext.ui import ObservedObject, Published

from lib.context import Context

if TYPE_CHECKING:
    from cogs.audio import AudioBase


class AudioViewModel(ObservedObject):
    def __init__(self, cog: 'AudioBase', ctx: Context):
        super().__init__()
        self.cog = cog
        self.ctx = ctx
        self.disconnected = Published(False)

    def get_prefix(self):
        return self.ctx.prefix

    async def disconnect(self, interaction: discord.Interaction):
        try:
            interaction.message.guild.voice_client.stop()
            await interaction.message.guild.voice_client.disconnect(force=True)
            self.cog.connecting_guilds.remove(interaction.message.guild.id)
        except AttributeError:
            pass
        self.disconnected = True
