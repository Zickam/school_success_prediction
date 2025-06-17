import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import asyncio
import logging

import logging_setup
import nest_asyncio
import uvicorn

from fastapi_app import app

logging_setup.init()

nest_asyncio.apply()


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
        log_level="info",
    )


if __name__ == "__main__":
    run()
