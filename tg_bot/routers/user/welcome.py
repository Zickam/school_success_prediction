import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from tg_bot.filters import IsPrivate, IsPrivateCallback
from tg_bot import keyboards

router = Router()
router.message.filter(IsPrivate())
router.callback_query.filter(IsPrivateCallback())


@router.message(Command("start"))
async def start(msg: Message, state: FSMContext):
    await msg.answer(
        "Привет! Это бот для оценки успехов школьников. Выбери кто ты:",
        reply_markup=keyboards.user.welcome.keyboardChooseRole()
    )


@router.callback_query(F.data.startswith("role|"))
async def setRole(call: CallbackQuery, state: FSMContext):
    # await
    ...