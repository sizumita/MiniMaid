from discord import Embed, Colour
from lib.context import Context
from typing import Optional


def make_poll_reserve_embed(ctx: Context) -> Embed:
    embed = Embed(
        title="投票を作成中です",
        description="しばらくお待ちください。"
    )
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url_as(format="png"))
    return embed


def make_poll_embed(ctx: Context, poll) -> Embed:
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
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
    embed.set_footer(
        text="リアクションで投票できます。"
             + ("匿名投票のため、投票後はリアクションが削除されます。" if poll.hidden else "")
    )
    return embed
