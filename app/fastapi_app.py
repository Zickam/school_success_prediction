import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi import Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session, Base, engine
from tg_bot.setup.auto_init import AutoInitializer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database models initialized")

    session = await get_session()
    async with session as db:
        initializer = AutoInitializer(db)
        await initializer.initialize()

    from app.routers import api_router, webhook_router

    app.include_router(api_router)

    app.include_router(webhook_router)

    yield


app = FastAPI(
    lifespan=lifespan,
    title="School Success Prediction API",
    description="API for managing schools, classes, subjects, and grades with ML-powered predictions",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():

    return {"status": "healthy"}
