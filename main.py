from os import environ

from bot import MiniMaid


bot = MiniMaid()

extensions = [
    "cogs.party",
    "cogs.team",
    "cogs.poll",
    "cogs.poll_manager"
]

for extension in extensions:
    bot.load_extension(extension)

bot.run(environ["BOT_TOKEN"])
