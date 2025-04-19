from __future__ import annotations
import os
import logging
import datetime

from fastapi import APIRouter
from fastapi import Response, Request, Query

router = APIRouter(tags=["Webhook"], prefix="/webhook")

logging.info(f"Initializing hidden router for webhooks: {router.prefix}. ({__file__})")


@router.get("/healthcheck")
async def dockerHealthCheck():
    return Response(status_code=200)

