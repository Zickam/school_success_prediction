import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from tg_bot.filters import IsPrivate, IsPrivateCallback
from tg_bot import keyboards
from tg_bot.config import httpx_client
from tg_bot.common import updateUserDecorator

router = Router()
router.message.filter(IsPrivate())
router.callback_query.filter(IsPrivateCallback())


@router.message(Command("start"))
@updateUserDecorator
async def start(msg: Message, state: FSMContext):
    class_uuid_to_join = msg.text.replace("/start ", "")
    if not class_uuid_to_join:
        await msg.answer("Привет! Это бот для оценки успехов школьников. Обратись к своему учителю для получения приглашения в класс!")
        return

    class_resp = await httpx_client.get("school/class", params={"uuid": class_uuid_to_join})
    if class_resp.status_code == 200:
        await msg.answer(
            f"Привет! Это бот для оценки успехов школьников. Тебя пригласили в класс: {class_resp.text}",
            reply_markup=keyboards.user.welcome.keyboardAcceptInvite(class_uuid_to_join)
        )
    else:
        await msg.answer(f"Привет! Это бот для оценки успехов школьников. Скорее всего с твоей ссылкой для приглашения в класс что-то не так, обратись к учителю за получением новой")


@router.callback_query(F.data.startswith("join|"))
@updateUserDecorator
async def joinClass(call: CallbackQuery, state: FSMContext):
    class_uuid = call.data.replace("join|", "")
    data = (await state.get_data())
    logging.info(data)
    resp = await httpx_client.post("school/class/student_join", params={"user_uuid": data["user_uuid"],
                                                                 "class_uuid": class_uuid})
    if resp.status_code == 409:
        await call.message.answer(f"Ты уже состоишь в этом классе")
    elif resp.status_code == 200:
        await call.message.answer(f"Ты присоединился к классу {resp.json()}")
    else:
        await call.message.answer(f"Произошла ошибка: {resp.status_code, resp.text}")