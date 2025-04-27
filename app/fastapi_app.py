from __future__ import annotations
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request, HTTPException, status, Depends


@asynccontextmanager
async def lifespan(app: FastAPI):
    from db.engine import init_models
    await init_models()

    from app.routers import webhook, auth, school, ml
    app.include_router(auth.router)
    app.include_router(webhook.router)
    app.include_router(school.router)
    app.include_router(ml.router)

    from app.routers import api_router
    app.include_router(api_router)

    yield

app = FastAPI(
    lifespan=lifespan,
    title="School Success Prediction API",
    description="API for managing schools, classes, subjects, and grades with ML-powered predictions",
    version="1.0.0"
)
