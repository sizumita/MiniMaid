from discord.ext.commands import (
    Cog,
    group,
    guild_only
)
from lib.database.query import create_poll, get_poll_by_id
from lib.embed import make_poll_embed, make_poll_reserve_embed, make_poll_result_embed
import discord
from lib.context import Context
import re
from emoji import UNICODE_EMOJI
from typing import TYPE_CHECKING, Optional, List, Tuple, Any
from lib.database.models import Poll

if TYPE_CHECKING:
    from bot import MiniMaid
emoji_compiled = re.compile(r"^<a?:[a-zA-Z0-9\_]+:([0-9]+)>$")

default_emojis = [
    "\N{REGIONAL INDICATOR SYMBOL LETTER A}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER B}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER C}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER D}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER E}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER F}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER G}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER H}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER I}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER J}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER K}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER L}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER M}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER N}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER O}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER P}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER Q}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER R}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER S}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER T}",
]


class PollCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot

    @staticmethod
    def is_emoji(text: str) -> bool:
        return text in UNICODE_EMOJI["en"].keys()  # type: ignore

    def is_discord_emoji(self, text: str) -> bool:
        match = emoji_compiled.match(text)
        if match is not None:
            emoji_id = match.group(1)
            emoji = self.bot.get_emoji(int(emoji_id))
            return emoji is not None
        return False

    def get_discord_emoji(self, text: str) -> discord.Emoji:
        if match := emoji_compiled.match(text):
            emoji_id = match.group(1)
            return self.bot.get_emoji(int(emoji_id))
        raise ValueError("Unknown Emoji")

    def parse_choices(self, choices: List[str]) -> List[Tuple[str, str]]:
        results = []
        if len(choices) > 20:
            raise ValueError("選択肢が20個を超えています。")
        for i, text in enumerate(choices):
            results.append((default_emojis[i], text))

        return results

    def parse_choices_with_emoji(self, choices: List[str]) -> List[Tuple[str, str]]:
        results = []
        while choices:
            emoji = choices.pop(0)
            if self.is_emoji(emoji):
                text = choices.pop(0)
                results.append((emoji, text))
                continue

            elif self.is_discord_emoji(emoji):
                emoji_o = self.get_discord_emoji(emoji)
                text = choices.pop(0)
                results.append((emoji_o, text))
                continue

            raise ValueError(f"絵文字がくるべきでしたが、絵文字ではありませんでした: {emoji}")

        return results

    def parse_args(self, *args: str) -> Tuple[bool, str, List[Tuple[Any, Any]]]:
        params = list(args)
        hidden = False
        first = params.pop(0)
        if first == "hidden":
            hidden = True
            title = params.pop(0)
        else:
            title = first

        if not params:
            return hidden, title, [("\U00002b55", "\U00002b55"), ("\U0000274c", "\U0000274c")]

        # parse choices
        if all(map(lambda x: self.is_emoji(x) or self.is_discord_emoji(x), params)):
            choices = []
            for emoji in params:
                if self.is_emoji(emoji):
                    choices.append((emoji, emoji))
                else:
                    emoji = self.get_discord_emoji(emoji)
                    choices.append((emoji, emoji))

            return hidden, title, choices

        if self.is_emoji(params[0]) or self.is_discord_emoji(params[0]):
            return hidden, title, self.parse_choices_with_emoji(params)
        return hidden, title, self.parse_choices(params)

    async def create_poll(self,
                          ctx: Context,
                          title: str,
                          choices: List[Tuple[Any, Any]],
                          limit: Optional[int] = None,
                          hidden: bool = False) -> None:
        """create poll"""

        poll_message = await ctx.embed(make_poll_reserve_embed(ctx))
        poll = create_poll(title, choices, limit, hidden, ctx.guild.id, ctx.channel.id, poll_message.id, ctx.author.id)
        async with self.bot.db.Session() as session:
            async with session.begin():
                session.add(poll)
        await poll_message.edit(embed=make_poll_embed(ctx, poll))
        for emoji, _ in choices:
            await poll_message.add_reaction(emoji)

    @group(invoke_without_command=True)
    @guild_only()
    async def poll(self, ctx: Context, *args: str) -> None:
        """
        投票を作成します。
        タイトルの前にhiddenと入力すると投票した瞬間にリアクションが消え投票を隠すことができます。
        次に、投票のタイトルを入れてください。
        その後に、投票の選択肢を20個までスペースを開けて入力してください。
        選択肢と絵文字を交互に入力した場合、それぞれの選択肢に絵文字が反映されます。
        絵文字を省略し選択肢のみを入力した場合、AからTまでの絵文字が代わりに使用されます。
        両方省略した場合⭕️❌の投票になります。
        絵文字のみを入力した場合、選択肢も絵文字になります。

        example:
            `poll 好きな果物 りんご みかん いちご`

            `poll hidden 推しVTuber がうるぐら 委員長 船長`

            `poll いちごは果物か？`

            `poll ねこ 😸 😻 😹`
        """
        params = []
        for arg in args:
            if len(arg) == 2:
                if self.is_emoji(arg[0]) and arg[1].encode() == b"\xef\xb8\x8f":
                    params.append(arg[0])
                    continue
            params.append(arg)

        is_hidden, title, choices = self.parse_args(*params)
        await self.create_poll(ctx, title, choices, None, is_hidden)

    @poll.error
    async def poll_error(self, ctx: Context, exception: Exception) -> None:
        if isinstance(exception, ValueError):
            await ctx.error(f"エラー: {exception.args[0]}")
        raise exception

    @poll.command(name="limited", aliases=["lim", "l"])
    async def limited_poll(self, ctx: Context, num: int, *args: str) -> None:
        """
        投票できる個数を制限した投票を作成します。
        `poll limited <投票可能数> [hidden] <投票タイトル> [[絵文字] [選択肢]]...`
        タイトルの前にhiddenと入力すると投票した瞬間にリアクションが消え投票を隠すことができます。
        次に、投票のタイトルを入れてください。
        その後に、投票の選択肢を20個までスペースを開けて入力してください。
        選択肢と絵文字を交互に入力した場合、それぞれの選択肢に絵文字が反映されます。
        絵文字を省略し選択肢のみを入力した場合、AからTまでの絵文字が代わりに使用されます。
        両方省略した場合⭕️❌の投票になります。
        絵文字のみを入力した場合、選択肢も絵文字になります。

        example:
            `poll limited 1 どのチームが優勝するか 楽天 巨人 広島`

            `poll limited 2 hidden 緯度が日本より上の国の２つはどれか？ 🇮🇹 イタリア 🇬🇧 イギリス 🇩🇪 ドイツ 🇫🇷 フランス`
        """
        is_hidden, title, choices = self.parse_args(*args)
        await self.create_poll(ctx, title, choices, num, is_hidden)

    @limited_poll.error
    async def limited_poll_error(self, ctx: Context, exception: Exception) -> None:
        if isinstance(exception, ValueError):
            await ctx.error(f"エラー: {exception.args[0]}")
        raise exception

    @poll.command(name="result")
    async def pull_result(self, ctx: Context, poll_id: int):
        async with self.bot.db.Session() as session:
            result = await session.execute(get_poll_by_id(poll_id))
            poll: Poll = result.scalars().first()
            if poll is None or poll.guild_id != ctx.guild.id:
                await ctx.error(f"ID: {poll_id}の投票が見つかりません。")
                await session.rollback()
                return

        if not poll.hidden:
            message = await self.bot.get_channel(poll.channel_id).fetch_message(poll.message_id)
            results = {}
            for reaction in message.reactions:
                results[str(reaction.emoji)] = len([i for i in await reaction.users().flatten() if not i.bot])
        else:
            results = {}
            for choice in poll.choices:
                results[choice.emoji] = len(choice.votes)

        result_choices = []
        all_vote_count = sum(results.values())
        for choice in poll.choices:
            result_choices.append(
                # choice, count, percent
                (choice, results[choice.emoji], 0 if results[choice.emoji] == 0 else results[choice.emoji] / all_vote_count * 100)
            )
        await ctx.embed(make_poll_result_embed(self.bot, ctx, poll, result_choices))


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(PollCog(bot))
