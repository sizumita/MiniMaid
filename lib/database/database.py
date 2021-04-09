import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from os import environ
from typing import Optional

from lib.database.base import Base


class Database:
    def __init__(self, loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()) -> None:
        self.loop = loop
        self.engine = create_async_engine(
            environ["DATABASE_URL"],
            echo=True,
        )
        self.Session: Optional[sessionmaker] = None

    async def start(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.Session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
