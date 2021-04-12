from discord.ext.commands import Cog
from sqlalchemy.future import select
from lib.database.models import Poll
from sqlalchemy.orm import selectinload

from typing import TYPE_CHECKING
import discord

if TYPE_CHECKING:
    from bot import MiniMaid


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
                    .options(selectinload(Poll.choices))
                result = await session.execute(query)
                poll = result.scalars().first()
                if poll is None:
                    return
                how_many_user_voted = sum([1 for c in poll.choices if payload.user_id in c.users])

                if poll.limit is not None:
                    if how_many_user_voted == poll.limit:
                        try:
                            await self.delete_reaction(payload)
                        except discord.Forbidden:
                            pass
                        return

                choice = [i for i in poll.choices if i.emoji == str(payload.emoji)][0]
                if payload.user_id in choice.users:
                    if poll.hidden:
                        users = list(choice.users)
                        users.remove(payload.user_id)
                        choice.users = users
                        await self.delete_reaction(payload)
                    else:
                        return
                else:
                    users = list(choice.users)
                    users.append(payload.user_id)
                    choice.users = users
                    if poll.hidden:
                        await self.delete_reaction(payload)


def setup(bot):
    return bot.add_cog(PollManagerCog(bot))
