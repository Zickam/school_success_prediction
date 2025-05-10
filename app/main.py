from __future__ import annotations
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import logging_setup
logging_setup.init()

import uvicorn
import nest_asyncio

nest_asyncio.apply()

from fastapi_app import app  # necessary for uvicorn


def run():
    ssl_keyfile = os.getenv("TLS_KEYFILE")
    ssl_certfile = os.getenv("TLS_CERTFILE")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8000")),
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    run()
