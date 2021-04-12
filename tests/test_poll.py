from lib.fake import FakeBot
from cogs.poll import PollCog, default_emojis


def test_parse_args_1():
    cog = PollCog(FakeBot())
    assert cog.parse_args("a", "b", "c") \
           == \
           (False, "a", [(default_emojis[0], "b"), (default_emojis[1], "c")])
