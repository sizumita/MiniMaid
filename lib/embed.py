from discord import Embed, Colour
from lib.context import Context
from lib.database.models import Poll
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import MiniMaid
MESSAGE_URL_BASE = "https://discord.com/channels/{0}/{1}/{2}"


def make_poll_reserve_embed(ctx: Context) -> Embed:
    embed = Embed(
        title="投票を作成中です",
        description="しばらくお待ちください。"
    )
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url_as(format="png", size=128))
    return embed


def make_poll_embed(ctx: Context, poll: Poll) -> Embed:
    description = f"{poll.limit}個まで投票できます。\n\n" if poll.limit is not None else ""
    for choice in poll.choices:
        if choice.emoji == choice.value:
            description += f"{choice.emoji}\n"
            continue
        description += f"{choice.emoji} {choice.value}\n"
    description += f"\n結果->`{ctx.prefix}poll result {poll.id}`"
    embed = Embed(
        title=poll.title,
        description=description,
        colour=Colour.blue()
    )
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url_as(format="png", size=128))
    embed.set_footer(
        text="リアクションで投票できます。"
             + ("匿名投票のため、投票後はリアクションが削除されます。" if poll.hidden else "")
    )
    return embed


def make_poll_result_embed(bot: 'MiniMaid', ctx: Context, poll: Poll, choices: list) -> Embed:
    message_url = MESSAGE_URL_BASE.format(poll.guild_id, poll.channel_id, poll.message_id)
    user = bot.get_user(poll.owner_id)
    embed = Embed(
        description=f"**[{poll.title}]({message_url})**",
        colour=Colour.dark_orange()
    )
    embed.set_author(name=(str(user) if user is not None else str(poll.owner_id)),
                     icon_url=(user.avatar_url_as(format="png", size=128) if user is not None else None))
    embed.set_footer(text=f"{ctx.prefix}poll end {poll.id} で投票を終了できます。")

    for choice, count, percent in choices:
        graph = '\U00002b1c' * int(percent//10)
        embed.add_field(
            name=f"{choice.emoji} {choice.value}  ({count}票)",
            value=f"{graph}  {int(percent)}%",
            inline=False
        )

    return embed
