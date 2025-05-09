import os
from pathlib import Path
import httpx
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from tg_bot.env
env_path = Path(__file__).parent.parent / "env" / "tg_bot.env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# Storage settings
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# API settings
API_URL = os.getenv("API_URL", "http://app:8443")  # Use correct port from app.env
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "30.0"))
API_RETRIES = int(os.getenv("API_RETRIES", "3"))
API_RETRY_DELAY = float(os.getenv("API_RETRY_DELAY", "1.0"))

# Create httpx client with retry logic
httpx_client = httpx.AsyncClient(
    base_url=API_URL,
    verify=False,  # Disable SSL verification for local development
    timeout=API_TIMEOUT,
    limits=httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10
    ),
    transport=httpx.AsyncHTTPTransport(
        retries=API_RETRIES,
        verify=False
    )
)

async def test_api_connection():
    """Test connection to the API"""
    logger.info(f"Testing connection to API at {API_URL}")
    try:
        response = await httpx_client.get("/health")
        response.raise_for_status()
        logger.info(f"Successfully connected to API at {API_URL}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to API at {API_URL}: {e}")
        return False