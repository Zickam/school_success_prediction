from aiogram import Router

from tg_bot.filters import IsPrivate

from tg_bot.routers.user import welcome, debug, statistics, grades

router = Router()

router.include_routers(welcome.router, debug.router, statistics.router, grades.router)
