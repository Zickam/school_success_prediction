from __future__ import annotations
import asyncio
import logging
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(os.path.join(SCRIPT_DIR, "../", "logging_setup.py")))

import logging_setup
logging_setup.init("logs/app.log")

import uvicorn
import nest_asyncio

nest_asyncio.apply()

from fastapi_app import app  # necessary for uvicorn


def run():
    if os.getenv("TLS_KEYFILE") and os.getenv("TLS_CERTFILE"):
        ssl_keyfile = os.getenv("TLS_KEYFILE")
        ssl_certfile = os.getenv("TLS_CERTFILE")
    else:
        ssl_keyfile = None
        ssl_certfile = None

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT")),
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    run()
