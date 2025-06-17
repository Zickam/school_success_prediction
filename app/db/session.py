import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


engine = create_async_engine(
    os.getenv("DB_URL"),
    echo=True,
    future=True,
    connect_args={"check_same_thread": False},
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class AsyncSessionManager:

    def __init__(self):
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        self.session = async_session_factory()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()


session_manager = AsyncSessionManager()


async def get_session() -> AsyncSession:

    return session_manager


class Base(DeclarativeBase):

    pass
