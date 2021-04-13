from discord import Embed, Colour
from lib.context import Context
from lib.database.models import Poll
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import MiniMaid
MESSAGE_URL_BASE = "https://discord.com/channels/{0}/{1}/{2}"
SYNTAX_MESSAGE = """
構文: `{prefix}poll [hidden] <投票のタイトル> [[絵文字 選択肢] [絵文字 選択肢]...]`
タイトルの前にhiddenと入力すると投票した瞬間にリアクションが消え投票を隠すことができます。
次に、投票のタイトルを入れてください。
その後に、投票の選択肢を20個までスペースを開けて入力してください。
選択肢と絵文字を交互に入力した場合、それぞれの選択肢に絵文字が反映されます。
絵文字を省略し選択肢のみを入力した場合、AからTまでの絵文字が代わりに使用されます。
両方省略した場合⭕️❌の投票になります。
絵文字のみを入力した場合、選択肢も絵文字になります。

```
example:
    {prefix}poll 好きな果物 りんご みかん いちご
    
    {prefix}poll hidden 推しVTuber がうるぐら 委員長 船長
    
    {prefix}poll いちごは果物か？
    
    {prefix}poll ねこ 😸 😻 😹
```
"""
LIMITED_MESSAGE = """
構文: `{prefix}poll limited <投票可能最大数> [hidden] <投票のタイトル> [[絵文字 選択肢] [絵文字 選択肢]...]`
投票できる個数を制限した投票を作成します。投票最大可能数までの個数の選択肢に投票できます。
後の構文は基本的な構文と同じです。
```
example:
    poll limited 1 どのチームが優勝するか 楽天 巨人 広島

    poll limited 2 hidden 緯度が日本より上の国の２つはどれか？ 🇮🇹 イタリア 🇬🇧 イギリス 🇩🇪 ドイツ 🇫🇷 フランス
```        
"""


def make_poll_help_embed(ctx: Context) -> Embed:
    embed = Embed(
        title="投票機能の使い方",
        colour=Colour.teal()
    )
    embed.add_field(
        name="投票の作成: 基本的な構文",
        value=SYNTAX_MESSAGE.format(prefix=ctx.prefix),
        inline=False
    )
    embed.add_field(
        name="投票の作成: 投票数を制限する",
        value=LIMITED_MESSAGE.format(prefix=ctx.prefix),
        inline=False
    )
    embed.add_field(
        name="投票の終了",
        value=f"`{ctx.prefix}poll end <投票ID>`\n投票を終了します。これ以降のリアクションの変更は無視されます。"
    )
    embed.add_field(
        name="投票の集計",
        value=f"`{ctx.prefix}poll result <投票ID>`\n投票の集計をします。投票を終了していた場合、終了時までの投票のみが集計されます。",
        inline=False
    )
    return embed


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
    description \
        += f"\n\n投票ID: {poll.id}\n結果->`{ctx.prefix}poll result {poll.id}`\n終了->`{ctx.prefix}poll end {poll.id}`\n"
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


def change_footer(embed: Embed, text: str) -> Embed:
    embed.set_footer(text=text)
    return embed
