from discord.ext import commands
import discord


class FakeBot(commands.Bot):
    def __init__(self) -> None:
        super(FakeBot, self).__init__("")

    def get_emoji(self, id: int) -> None:
        pass
