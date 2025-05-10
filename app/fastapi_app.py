from __future__ import annotations
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from tg_bot.env
env_path = Path(__file__).parent.parent / "env" / "tg_bot.env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

from fastapi import FastAPI, Depends
from fastapi import Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session, Base, engine
from app.routers import api_router, webhook_router
from tg_bot.setup.auto_init import AutoInitializer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database models and demo data initialization"""
    # Initialize database models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database models initialized")

    # Initialize demo data
    session = await get_session()
    async with session as db:
        initializer = AutoInitializer(db)
        await initializer.initialize()
    yield

app = FastAPI(
    lifespan=lifespan,
    title="School Success Prediction API",
    description="API for managing schools, classes, subjects, and grades with ML-powered predictions",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Include authenticated router
app.include_router(api_router)

# Include webhook router without prefix (it already has one)
app.include_router(webhook_router)
