from discord.ext import commands
import discord


class MiniMaid(commands.Bot):
    def __init__(self):
        super(MiniMaid, self).__init__(
            command_prefix="",
            intents=discord.Intents.all(),
            help_command=None
        )
