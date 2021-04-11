from lib.database.base import Base
from datetime import datetime
from sqlalchemy import (
    Integer,
    BigInteger,
    Column,
    String,
    ARRAY,
    DateTime
)


class Party(Base):
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    guild_id = Column(BigInteger)
    members = Column(ARRAY(BigInteger))
    owner_id = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)
