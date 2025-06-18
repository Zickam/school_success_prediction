import os
import logging
import asyncio
import time

import aiogram
import httpx
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from tg_bot.utilities import CustomAsyncClient


redis = Redis(host="redis")


tg_bot_secret = os.getenv("BOT_TOKEN")

bot = Bot(
    token=tg_bot_secret,
    default=DefaultBotProperties(parse_mode=aiogram.enums.ParseMode.HTML),
)

bot.redis = redis

storage = RedisStorage(redis)

dp = Dispatcher(storage=storage)

DATA_TRANSFER_PROTOCOL = "https" if os.getenv("TLS_KEYFILE") and os.getenv("TLS_CERTFILE") else "http"
base_url = f"{DATA_TRANSFER_PROTOCOL}://app:{os.getenv('API_PORT')}/"
# verify=False because this shit is used locally only
httpx_client = CustomAsyncClient(
    base_url=base_url,
    verify=False
)