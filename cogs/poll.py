from discord.ext.commands import (
    Cog,
    group
)
from lib.context import Context

from emoji import UNICODE_EMOJI
from typing import TYPE_CHECKING, Optional, List, Tuple
if TYPE_CHECKING:
    from bot import MiniMaid


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

    def is_emoji(self, text):
        # TODO: discordで追加された絵文字かどうかの判定
        return text in UNICODE_EMOJI

    def parse_choices(self, choices: List[str]):
        results = []
        if len(choices) > 20:
            raise ValueError("選択肢が20個を超えています。")
        for i, text in enumerate(choices):
            results.append((default_emojis[i], text))

        return results

    def parse_choices_with_emoji(self, choices: List[str]):
        results = []
        while choices:
            emoji = choices.pop(0)
            if not self.is_emoji(emoji):
                raise ValueError(f"絵文字がくるべきでしたが、絵文字ではありませんでした: {emoji}")
            text = choices.pop(0)
            results.append((emoji, text))

        return results

    def parse_args(self, *args: str):
        args = list(args)
        hidden = False
        first = args.pop(0)
        if first == "hidden":
            hidden = True
            title = args.pop(0)
        else:
            title = first

        if not args:
            return hidden, title, [("\U00002b55", "\U00002b55"), ("\U0000274c", "\U0000274c")]

        # parse choices
        if all(map(self.is_emoji, args)):
            return hidden, title, [(i, i) for i in args]

        if self.is_emoji(args[0]):
            return hidden, title, self.parse_choices_with_emoji(args)
        return hidden, title, self.parse_choices(args)

    async def create_poll(self,
                          ctx: Context,
                          title: str,
                          choices: List[Tuple[str, str]],
                          limit: Optional[int] = None,
                          hidden: bool = False):
        # TODO 書く
        pass

    @group()
    async def poll(self, ctx: Context, *args: tuple):
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
        is_hidden, title, choices = self.parse_args(*args)
        await self.create_poll(ctx, title, choices, None, is_hidden)

    @poll.error()
    async def poll_error(self, ctx: Context, exception: Exception):
        if isinstance(exception, ValueError):
            await ctx.error(f"エラー: {exception.args[0]}")

    @poll.command(name="limited", aliases=["lim", "l"])
    async def limited_poll(self, ctx: Context, num: int, *args: tuple):
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

    @limited_poll.error()
    async def limited_poll_error(self, ctx: Context, exception: Exception):
        if isinstance(exception, ValueError):
            await ctx.error(f"エラー: {exception.args[0]}")


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(PollCog(bot))
