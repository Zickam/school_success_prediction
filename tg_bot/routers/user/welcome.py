import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from tg_bot.filters import IsPrivate, IsPrivateCallback

router = Router()
router.message.filter(IsPrivate())
router.callback_query.filter(IsPrivateCallback())


@router.message(Command("start"))
async def start(msg: Message, state: FSMContext):
    await msg.answer("Привет! Это бот для оценки твоих успехов")

