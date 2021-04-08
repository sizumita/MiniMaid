import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from os import environ

from lib.database.base import Base


class Database:
    def __init__(self, loop: asyncio.BaseEventLoop = asyncio.get_event_loop()):
        self.loop = loop
        self.engine = create_async_engine(
            environ["DATABASE_URL"],
            echo=True,
        )
        self.session = None

    async def start(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
