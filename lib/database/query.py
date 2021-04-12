from sqlalchemy.future import select
from sqlalchemy.sql import Select
from lib.database.models import Party, Poll, Choice
from typing import Optional


def select_party(guild_id: int, name: str) -> Select:
    return select(Party).where(Party.guild_id == guild_id).where(Party.name == name)


def select_parties(guild_id: int) -> Select:
    return select(Party).where(Party.guild_id == guild_id)


def create_poll(
        title: str,
        choices: list,
        limit: Optional[int],
        hidden: bool,
        guild_id: int,
        channel_id: int,
        message_id: int,
        owner_id: int) -> Poll:
    return Poll(
        title=title,
        limit=limit,
        hidden=hidden,
        choices=[Choice(emoji=str(emoji), value=str(value)) for (emoji, value) in choices],
        guild_id=guild_id,
        channel_id=channel_id,
        message_id=message_id,
        owner_id=owner_id
    )
