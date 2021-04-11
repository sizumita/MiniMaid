from bot import MiniMaid
from os import environ


bot = MiniMaid()

extensions = [
    "cogs.party"
]

for extension in extensions:
    bot.load_extension(extension)

bot.run(environ["BOT_TOKEN"])
