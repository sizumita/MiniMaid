from bot import MiniMaid
from os import environ


bot = MiniMaid()

bot.run(environ["BOT_TOKEN"])
