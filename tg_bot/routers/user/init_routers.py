from aiogram import Router

from tg_bot.filters import IsPrivate

from tg_bot.routers.user import welcome, debug

router = Router()

router.include_routers(
    welcome.router,
    debug.router
)
