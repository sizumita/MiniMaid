import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict

from discord.ext.commands import Cog
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import discord
from discord.message import convert_emoji_reaction

from lib.database.models import Poll, Choice, Vote

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
        message: discord.Message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if message.author.id != self.bot.user.id:
            return
        r = await self.vote_add_action(payload)
        if r is None:
            return
        if r.limit is None:
            return
        choice_emojis = [i.emoji for i in r.choices]
        if str(payload.emoji) not in choice_emojis:
            return
        if payload.user_id not in self.locks.keys():
            self.locks[payload.user_id] = asyncio.Lock()

        async with self.locks[payload.user_id]:
            count = 0
            reactions = []
            for reaction in message.reactions:
                users = await reaction.users(limit=1, after=FakeUser(payload.user_id - 1)).flatten()
                if not users:
                    continue
                if users[0].id == payload.user_id:
                    count += 1
                    if str(payload.emoji) != str(reaction.emoji):
                        reactions.append(reaction.emoji)
            if count > r.limit:
                if reactions:
                    await message.remove_reaction(reactions[0], member)

    @Cog.listener(name="on_raw_reaction_remove")
    async def watch_vote_remove(self, payload: discord.RawReactionActionEvent) -> None:
        member = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
        if member.bot:
            return
        if not isinstance(self.bot.get_channel(payload.channel_id), discord.TextChannel):
            return
        message: discord.Message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if message.author.id != self.bot.user.id:
            return
        r = await self.vote_remove_action(payload)
        if r is None:
            return
        if r.limit is None:
            return
        choice_emojis = [i.emoji for i in r.choices]
        if str(payload.emoji) not in choice_emojis:
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
                if poll is None:
                    return poll
                if poll.ended_at is not None and poll.ended_at <= datetime.utcnow():
                    return None
                if not poll.hidden:
                    return poll

                all_votes = []
                choices = {}
                for choice in poll.choices:
                    all_votes += choice.votes
                    choices[str(choice.emoji)] = choice

                if str(payload.emoji) not in choices.keys():
                    return None
                all_my_votes = [i for i in all_votes if i.user_id == payload.user_id]

                same_emoji_votes = [i for i in all_my_votes if i.choice.emoji == str(payload.emoji)]
                if any(same_emoji_votes):
                    await session.delete(same_emoji_votes[0])
                    await self.delete_reaction(payload)
                    return None

                if poll.limit is not None and len(all_my_votes) >= poll.limit:
                    await session.delete(all_my_votes[0])
                    session.add(Vote(choice_id=choices[str(payload.emoji)].id, user_id=payload.user_id))
                    await self.delete_reaction(payload)
                    return None

                session.add(Vote(choice_id=choices[str(payload.emoji)].id, user_id=payload.user_id))
                await self.delete_reaction(payload)

        return None

    async def delete_reaction(self, payload: discord.RawReactionActionEvent) -> None:
        self.bot.loop.create_task(self.bot.http.remove_reaction(
            payload.channel_id,
            payload.message_id,
            convert_emoji_reaction(payload.emoji),
            payload.user_id
        ))

    async def vote_remove_action(self, payload: discord.RawReactionActionEvent) -> Optional[Poll]:
        async with self.bot.db.SerializedSession() as session:
            async with session.begin():
                query = select(Poll)\
                    .filter_by(guild_id=payload.guild_id, channel_id=payload.channel_id, message_id=payload.message_id)\
                    .options(selectinload(Poll.choices).selectinload(Choice.votes))
                result = await session.execute(query)
                poll = result.scalars().first()
                if poll is None:
                    return poll
                if poll.ended_at is not None and poll.ended_at <= datetime.utcnow():
                    return None
                if not poll.hidden:
                    return poll
        return None


def setup(bot: 'MiniMaid') -> None:
    return bot.add_cog(PollManagerCog(bot))
