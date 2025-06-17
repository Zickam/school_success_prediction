import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand

from tg_bot.config import BOT_TOKEN, USE_REDIS, test_api_connection
from tg_bot.routers.user.init_routers import router as user_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):

    return
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Показать справку"),
        BotCommand(command="menu", description="Показать меню"),
        BotCommand(command="statistics", description="Просмотр статистики"),
        BotCommand(command="grades", description="Просмотр оценок"),
    ]
    await bot.set_my_commands(commands)


async def main():

    if not await test_api_connection():
        logger.error(
            "Failed to connect to API. Please check if the API is running and accessible."
        )
        return

    bot = Bot(token=BOT_TOKEN)

    if USE_REDIS:
        storage = RedisStorage.from_url("redis://redis:6379/0")
    else:
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)

    dp.include_router(user_router)

    await set_commands(bot)

    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
