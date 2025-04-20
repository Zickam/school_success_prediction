import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from tg_bot.filters import IsPrivate, IsPrivateCallback
from tg_bot import keyboards
from tg_bot.config import httpx_client

router = Router()
router.message.filter(IsPrivate())
router.callback_query.filter(IsPrivateCallback())


@router.message(Command("start"))
async def start(msg: Message, state: FSMContext):
    class_id_to_join = msg.text.replace("/start ", "")

    class_description = await httpx_client.get("class", params={"id": class_id_to_join})

    await msg.answer(
        f"Привет! Это бот для оценки успехов школьников. Тебя пригласили в класс: {class_description.text}",
        reply_markup=keyboards.user.welcome.keyboardAcceptInvite(class_id_to_join)
    )


# @router.callback_query(F.data.startswith("role|"))
# async def setRole(call: CallbackQuery, state: FSMContext):
#     # await
#     ...
#
# @router.inline_query()
# async def showSchools