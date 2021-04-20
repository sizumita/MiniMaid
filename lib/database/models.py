# type: ignore
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
    Boolean,
    Float,
    UniqueConstraint
)

from lib.database.base import Base


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
    votes = relationship("Vote")  # 投票したユーザー

    created_at = Column(DateTime, default=datetime.utcnow)


class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True)
    choice_id = Column(Integer, ForeignKey('choices.id'))
    choice = relationship("Choice", back_populates="votes")

    user_id = Column(BigInteger)

    created_at = Column(DateTime, default=datetime.utcnow)


class UserVoicePreference(Base):
    __tablename__ = "user_voice_preference"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True)

    speed = Column(Float, default=1.0)  # 速さ 0.5 < s < 2.0
    tone = Column(Float, default=0)  # トーン -20.0 < t < 20.0
    intone = Column(Float, default=1.0)  # イントネーション 0.0 < i < 4.0
    volume = Column(Float, default=-3.0)  # 大きさ -20.0 < v < 0.0


class GuildVoicePreference(Base):
    __tablename__ = "guild_voice_preference"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, unique=True)

    read_name = Column(Boolean, default=True)
    read_join = Column(Boolean, default=False)
    read_leave = Column(Boolean, default=False)
    read_bot = Column(Boolean, default=False)
    read_nick = Column(Boolean, default=True)
    limit = Column(Integer, default=100)


class VoiceDictionary(Base):
    __tablename__ = "voice_dictionaries"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, unique=True)

    before = Column(String, unique=True)
    after = Column(String)

    owner_id = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)


class AudioTag(Base):
    __tablename__ = "audio_tags"
    __table_args__ = (UniqueConstraint('guild_id', 'name'), {})
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, nullable=False)

    name = Column(String, nullable=False)
    audio_url = Column(String, nullable=False)

    owner_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Feed(Base):
    __tablename__ = "feeds"
    id = Column(Integer, primary_key=True)

    url = Column(String, unique=True, nullable=False)
    readers = relationship("Reader")
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 最終更新時
    available = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Reader(Base):
    __tablename__ = "readers"
    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey('feeds.id'), nullable=False)
    feed = relationship("Feed", back_populates="readers")

    channel_id = Column(BigInteger, nullable=False)

    owner_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
