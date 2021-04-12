from discord.ext.commands import Cog
from sqlalchemy.future import select
from lib.database.models import Poll, Choice, Vote
from sqlalchemy.orm import selectinload

from typing import TYPE_CHECKING
import discord

if TYPE_CHECKING:
    from bot import MiniMaid


def is_voted(user_id: int, choice: Choice):
    for x in choice.votes:
        if x.user_id == user_id:
            return True
    return False


class PollManagerCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot
        self.listening_messages = []

    async def delete_reaction(self, payload: discord.RawReactionActionEvent):
        message: discord.Message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        self.bot.loop.create_task(message.remove_reaction(
            payload.emoji,
            self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
        ))

    @Cog.listener(name="on_raw_reaction_add")
    async def watch_vote(self, payload: discord.RawReactionActionEvent):
        """
        1. 個数制限がある場合
            1.. 個数制限の上限になっている場合
                1... hiddenの場合
                    1.... すでに投票している選択肢の場合、voteを消してリアクションを消してend
                    2.... リアクションを消してend
                2... 投票している選択肢の場合、何もせずend
                3... 投票していない選択肢の場合、リアクションを消してend
            2.. すでに投票している選択肢の場合、何もせずend
            3.. 投票していない選択肢の場合、voteを増やしてend
        """
        user = self.bot.get_user(payload.user_id)
        if user.bot:
            return
        if not isinstance(self.bot.get_channel(payload.channel_id), discord.TextChannel):
            return

        async with self.bot.db.Session() as session:
            async with session.begin(subtransactions=True):
                query = select(Poll)\
                    .filter_by(guild_id=payload.guild_id, channel_id=payload.channel_id, message_id=payload.message_id) \
                    .with_for_update()\
                    .options(selectinload(Poll.choices).selectinload(Choice.votes))
                result = await session.execute(query)
                poll = result.scalars().first()
                if poll is None:
                    return

                voted_choices = [choice for choice in poll.choices if is_voted(payload.user_id, choice)]

                if poll.limit is not None:
                    if len(voted_choices) >= poll.limit:
                        targets = [i for i in voted_choices if i.emoji == str(payload.emoji)]
                        if targets:
                            if poll.hidden:
                                await session.delete(targets[0])
                                await self.delete_reaction(payload)
                            return
                        await self.delete_reaction(payload)
                        return

                targets = [i for i in voted_choices if i.emoji == str(payload.emoji)]

                if targets:
                    if poll.hidden:
                        await session.delete(targets[0])
                        await self.delete_reaction(payload)
                    return

                targets = [i for i in poll.choices if i.emoji == str(payload.emoji)]
                if not targets:
                    return

                session.add(Vote(choice_id=targets[0].id, user_id=payload.user_id))
                if poll.hidden:
                    await self.delete_reaction(payload)


def setup(bot):
    return bot.add_cog(PollManagerCog(bot))
