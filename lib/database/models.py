from lib.database.base import Base
from sqlalchemy import (
    Integer,
    BigInteger,
    Column
)


class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    command_channel_id = Column(BigInteger)
