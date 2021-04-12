from lib.fake import FakeBot, FakeEmoji
from cogs.poll import PollCog, default_emojis


def test_parse_args_1():
    cog = PollCog(FakeBot())
    assert cog.parse_args("a", "b", "c") \
           == \
           (False, "a", [(default_emojis[0], "b"), (default_emojis[1], "c")])


def test_parse_args_2():
    cog = PollCog(FakeBot())
    assert cog.parse_args("hidden", "a", "b", "c") \
           == \
           (True, "a", [(default_emojis[0], "b"), (default_emojis[1], "c")])


def test_parse_args_3():
    cog = PollCog(FakeBot())
    assert cog.parse_args("hidden", "a", "<:test_emoji:1>", "b", "\U0000274c", "c") \
           == \
           (True, "a", [(FakeEmoji(1), "b"), ("\U0000274c", "c")])


def test_parse_args_4():
    cog = PollCog(FakeBot())
    assert cog.parse_args("hidden", "a", "\U00002b55", "b", "\U0000274c", "c") \
           == \
           (True, "a", [("\U00002b55", "b"), ("\U0000274c", "c")])


def test_is_emoji_1():
    cog = PollCog(FakeBot())
    assert cog.is_emoji("\U00002b55")
