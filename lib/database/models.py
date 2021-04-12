from lib.database.base import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Integer,
    BigInteger,
    Column,
    String,
    ARRAY,
    DateTime,
    ForeignKey,
    Boolean
)


class Party(Base):
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    guild_id = Column(BigInteger)
    members = Column(ARRAY(BigInteger))
    owner_id = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)


class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True)
    title = Column(String)  # 投票のタイトル
    choices = relationship("Choice")  # 投票の選択肢
    limit = Column(Integer, nullable=True)  # 投票できる個数の制限
    hidden = Column(Boolean, default=False)  # 投票したときにリアクションを消して秘匿するか

    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    message_id = Column(BigInteger)
    owner_id = Column(BigInteger)

    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)  # 投票が終わった時刻


class Choice(Base):
    __tablename__ = "choices"

    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey('polls.id'))
    poll = relationship("Poll", back_populates="choices")

    emoji = Column(String)  # 投票用の絵文字
    value = Column(String)  # 選択肢のテキスト
    users = Column(ARRAY(BigInteger))  # 投票したユーザー

    created_at = Column(DateTime, default=datetime.utcnow)
