import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from tg_bot.filters import IsPrivate, IsPrivateCallback

router = Router()
router.message.filter(IsPrivate())
router.callback_query.filter(IsPrivateCallback())


@router.message()
async def unexpectedMsg(msg: Message, state: FSMContext):
    logging.info(msg)
    await msg.answer(f"[DEBUG] Unexpected message: {msg.text}")


@router.callback_query()
async def unexpectedCallback(call: CallbackQuery, state: FSMContext):
    logging.info(call)
    await call.message.answer(f"[DEBUG] Unexpected callback: {call.data}")

