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
    # from db import utilities
    # import db
    # from scheduler.init import async_scheduler
    #
    # await utilities.initSchemasAndTortoise(
    #     db.TORTOISE_ORM_CONFIG
    # )  # it is crucial to place it before any routers initialization because we need to fully initialize models first
    #
    # from db import utilities
    # from db import TORTOISE_ORM_CONFIG
    # import asyncio
    # asyncio.run(utilities.initSchemasAndTortoise(
    #     TORTOISE_ORM_CONFIG))  # BE VERY CAREFUL WITH THIS BECAUSE IT HELPS THE OPENAPI TO DETECT ALL THE INCLUDED FIELDS

    from app.routers import api_router

    app.include_router(api_router)

    # async_scheduler.start()

    yield

app = FastAPI(
    lifespan=lifespan,
    # dependencies=[SessionDep]
)
