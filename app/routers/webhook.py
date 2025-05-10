from __future__ import annotations
import os
import logging
import datetime

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse

webhook_router = APIRouter(tags=["Webhook"], prefix="/webhook")

logging.info(f"Initializing hidden router for webhooks: {webhook_router.prefix}. ({__file__})")


@webhook_router.get("/healthcheck")
async def webhook_healthcheck():
    """Health check endpoint for webhook"""
    return {"status": "ok"}

@webhook_router.post("/")
async def webhook(request: Request):
    """Handle incoming webhook requests"""
    try:
        # Get the request body
        body = await request.json()
        logging.info(f"Received webhook: {body}")
        
        # Process the webhook
        # TODO: Implement webhook processing logic
        
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        logging.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )

