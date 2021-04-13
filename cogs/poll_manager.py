from discord.ext.commands import Cog
from sqlalchemy.future import select
from lib.database.models import Poll, Choice, Vote
from sqlalchemy.orm import selectinload

from typing import TYPE_CHECKING, Optional, Dict
import asyncio
import discord

if TYPE_CHECKING:
    from bot import MiniMaid


def is_voted(user_id: int, choice: Choice) -> bool:
    for x in choice.votes:
        if x.user_id == user_id:
            return True
    return False


def get_my_vote(user_id: int, choice: Choice) -> Optional[Vote]:
    for x in choice.votes:
        if x.user_id == user_id:
            return x
    return None


class FakeUser:
    def __init__(self, _id: int) -> None:
        self.id = _id


class PollManagerCog(Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot
        self.locks: Dict[str, asyncio.Lock] = {}

    @Cog.listener(name="on_raw_reaction_add")
    async def watch_vote_add(self, payload: discord.RawReactionActionEvent) -> None:
        """
        1... hiddenの場合
            1.... すでに投票している選択肢の場合、voteを消してリアクションを消してend
                2.... リアクションを消してend
            2... 投票している選択肢の場合、何もせずend
            3... 投票していない選択肢の場合、リアクションを消してend
        """
        member = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
        if member.bot:
            return
        if not isinstance(self.bot.get_channel(payload.channel_id), discord.TextChannel):
            return
        r = await self.vote_add_action(payload)
        if r is None:
            return
        if r.limit is None:
            return
        if payload.user_id not in self.locks.keys():
            self.locks[payload.user_id] = asyncio.Lock()

        async with self.locks[payload.user_id]:
            count = 0
            message: discord.Message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            for reaction in message.reactions:
                users = await reaction.users(limit=1, after=FakeUser(payload.user_id - 1)).flatten()
                if not users:
                    continue
                if users[0].id == payload.user_id:
                    count += 1
            if count > r.limit:
                await message.remove_reaction(payload.emoji, member)

    @Cog.listener(name="on_raw_reaction_remove")
    async def watch_vote_remove(self, payload: discord.RawReactionActionEvent) -> None:
        member = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
        if member.bot:
            return
        if not isinstance(self.bot.get_channel(payload.channel_id), discord.TextChannel):
            return
        r = await self.vote_remove_action(payload)
        if r is None:
            return
        if r.limit is None:
            return
        if payload.user_id not in self.locks.keys():
            self.locks[payload.user_id] = asyncio.Lock()

        async with self.locks[payload.user_id]:
            pass

    async def vote_add_action(self, payload: discord.RawReactionActionEvent) -> Optional[Poll]:
        async with self.bot.db.SerializedSession() as session:
            async with session.begin():

                query = select(Poll)\
                    .filter_by(guild_id=payload.guild_id, channel_id=payload.channel_id, message_id=payload.message_id) \
                    .options(selectinload(Poll.choices).selectinload(Choice.votes))
                result = await session.execute(query)
                poll = result.scalars().first()
                if poll is None or not poll.hidden:
                    return poll

                voted_choices = [choice for choice in poll.choices if is_voted(payload.user_id, choice)]

                if poll.limit is not None:
                    if len(voted_choices) >= poll.limit:
                        targets = [i for i in voted_choices if i.emoji == str(payload.emoji)]
                        if targets:
                            if poll.hidden:
                                vote = get_my_vote(payload.user_id, targets[0])
                                if vote is not None:
                                    await session.delete(vote)
                                await self.delete_reaction(payload)
                            return None
                        await self.delete_reaction(payload)
                        return None

                targets = [i for i in voted_choices if i.emoji == str(payload.emoji)]

                if targets:
                    if poll.hidden:
                        vote = get_my_vote(payload.user_id, targets[0])
                        if vote is not None:
                            await session.delete(vote)
                        await self.delete_reaction(payload)
                    return None

                targets = [i for i in poll.choices if i.emoji == str(payload.emoji)]
                if not targets:
                    return None

                session.add(Vote(choice_id=targets[0].id, user_id=payload.user_id))
                if poll.hidden:
                    await self.delete_reaction(payload)
        return None

    async def delete_reaction(self, payload: discord.RawReactionActionEvent) -> None:
        message: discord.Message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        self.bot.loop.create_task(message.remove_reaction(
            payload.emoji,
            self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
        ))

    async def vote_remove_action(self, payload: discord.RawReactionActionEvent) -> Optional[Poll]:
        async with self.bot.db.SerializedSession() as session:
            async with session.begin():
                query = select(Poll)\
                    .filter_by(guild_id=payload.guild_id, channel_id=payload.channel_id, message_id=payload.message_id) \
                    .options(selectinload(Poll.choices).selectinload(Choice.votes))
                result = await session.execute(query)
                poll = result.scalars().first()
                if poll is None or poll.hidden:
                    return poll

                targets = [i for i in poll.choices if is_voted(payload.user_id, i)]
                if targets:
                    vote = get_my_vote(payload.user_id, targets[0])
                    await session.delete(vote)
        return None


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(PollManagerCog(bot))
