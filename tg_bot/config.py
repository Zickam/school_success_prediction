import os
import logging
import asyncio
import time

import aiogram
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

redis = Redis(host="redis")


tg_bot_secret = os.getenv("BOT_TOKEN")

bot = Bot(
    token=tg_bot_secret,
    default=DefaultBotProperties(parse_mode=aiogram.enums.ParseMode.HTML),
)

bot.redis = redis

storage = RedisStorage(redis)

dp = Dispatcher(storage=storage)
