from discord.ext import commands


class FakeBot(commands.Bot):
    def __init__(self):
        super(FakeBot, self).__init__("")

    def get_emoji(self, id):
        pass
