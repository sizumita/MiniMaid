from sqlalchemy.future import select
from sqlalchemy.sql import Select
from lib.database.models import Party


def select_party(guild_id: int, name: str) -> Select:
    return select(Party).where(Party.guild_id == guild_id).where(Party.name == name)


def select_parties(guild_id: int) -> Select:
    return select(Party).where(Party.guild_id == guild_id)