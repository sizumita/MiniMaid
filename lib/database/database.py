import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from os import environ
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from lib.database.base import Base  # noqa


class Database:
    def __init__(self, loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()) -> None:
        self.loop = loop
        self.engine = create_async_engine(
            environ["DATABASE_URL"],
            # echo=True,
        )
        self.serialized_engine = self.engine.execution_options(isolation_level="SERIALIZABLE")
        self.Session: Optional[sessionmaker] = None
        self.SerializedSession: Optional[sessionmaker] = None

    async def start(self) -> None:
        self.Session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        self.SerializedSession = sessionmaker(
            self.serialized_engine, expire_on_commit=False, class_=AsyncSession
        )
