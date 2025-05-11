import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Get database URL from environment variable or use default SQLite
# DATABASE_URL = "sqlite+aiosqlite:///./school_success.db"

# Create async engine
engine = create_async_engine(
    os.getenv("DB_URL"),
    echo=True,
    future=True,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class AsyncSessionManager:
    """Async context manager for database sessions"""
    def __init__(self):
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        self.session = async_session_factory()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

# Create a global session manager instance
session_manager = AsyncSessionManager()

async def get_session() -> AsyncSession:
    """Get database session"""
    return session_manager

class Base(DeclarativeBase):
    """Base class for all models"""
    pass 