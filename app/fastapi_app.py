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

from fastapi import FastAPI
from fastapi import Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import getSession
from app.routers import (
    api_router,
    auth_router,
    user_router,
    school_router,
    class_router,
    subject_router,
    grade_router,
    invitation_router,
    webhook_router
)
from app.telegram.setup.auto_init import AutoInitializer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.engine import init_models
    await init_models()
    logger.info("Database models initialized")

    # Initialize demo data
    session_gen = getSession()
    try:
        session = await anext(session_gen)
        try:
            auto_init = AutoInitializer(session)
            await auto_init.initialize()
            logger.info("Demo data initialized successfully")
        finally:
            await session.close()
    except Exception as e:
        logger.error(f"Failed to initialize demo data: {e}")
        raise
    finally:
        await session_gen.aclose()

    # Include routers
    app.include_router(webhook_router)  # Include webhook router directly to bypass auth
    app.include_router(auth_router)     # Include auth router directly to bypass auth
    app.include_router(api_router)      # Include main API router with authentication
    logger.info("Routers included")

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
    status = {
        "status": "ok",
        "timestamp": time.time()
    }
    logger.info(f"Health check: {status}")
    return status
