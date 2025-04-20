import os
from typing import Annotated

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncAttrs
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from fastapi import Depends, FastAPI, HTTPException, Query


engine = create_async_engine(os.getenv("DB_URL"), echo=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base(cls=AsyncAttrs)

# Dependency for FastAPI
async def getSession() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

async def init_models():
    from . import declaration # it has to be there!!!!
    _ = lambda __: declaration # IT IS PLACED HERE FOR declaration module persistence here

    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

# SessionDep = Annotated[Session, Depends(getSession)]