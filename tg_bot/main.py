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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    """Set bot commands"""
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Показать справку"),
        BotCommand(command="menu", description="Показать меню"),
        BotCommand(command="statistics", description="Просмотр статистики"),
        BotCommand(command="grades", description="Просмотр оценок")
    ]
    await bot.set_my_commands(commands)

async def main():
    """Main function"""
    # Test API connection
    if not await test_api_connection():
        logger.error("Failed to connect to API. Please check if the API is running and accessible.")
        return

    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    
    # Use Redis storage if enabled, otherwise use memory storage
    if USE_REDIS:
        storage = RedisStorage.from_url("redis://redis:6379/0")
    else:
        storage = MemoryStorage()
    
    dp = Dispatcher(storage=storage)
    
    # Include routers
    dp.include_router(user_router)
    
    # Set bot commands
    await set_commands(bot)
    
    # Start polling
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
