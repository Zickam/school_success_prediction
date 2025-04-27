import logging
from uuid import UUID

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
    # Get command arguments
    args = msg.text.split()
    if len(args) == 1:  # Just /start
        await msg.answer(
            "Привет! Это бот для оценки успехов школьников. "
            "Обратись к своему учителю для получения приглашения в класс!"
        )
        return

    # Try to parse class UUID
    try:
        class_uuid = UUID(args[1])
    except ValueError:
        await msg.answer(
            "Привет! Это бот для оценки успехов школьников. "
            "Скорее всего с твоей ссылкой для приглашения в класс что-то не так, "
            "обратись к учителю за получением новой"
        )
        return

    # Get class info
    class_resp = await httpx_client.get(
        f"schools/classes/{str(class_uuid)}"
    )

    if class_resp.status_code == 200:
        class_info = class_resp.json()
        await msg.answer(
            f"Привет! Это бот для оценки успехов школьников. "
            f"Тебя пригласили в класс: {class_info['class_name']}",
            reply_markup=keyboards.user.welcome.keyboardAcceptInvite(str(class_uuid))
        )
    else:
        await msg.answer(
            "Привет! Это бот для оценки успехов школьников. "
            "Скорее всего с твоей ссылкой для приглашения в класс что-то не так, "
            "обратись к учителю за получением новой"
        )


@router.callback_query(F.data.startswith("join|"))
@updateUserDecorator
async def joinClass(call: CallbackQuery, state: FSMContext):
    try:
        class_uuid = call.data.replace("join|", "")
        data = await state.get_data()
        
        if "user_uuid" not in data:
            await call.message.answer("Ошибка: пользователь не найден. Попробуйте перезапустить бота командой /start")
            return

        resp = await httpx_client.post(
            f"schools/classes/{class_uuid}/join",
            params={
                "user_uuid": data["user_uuid"]
            }
        )

        if resp.status_code == 409:
            await call.message.answer("Ты уже состоишь в этом классе")
        elif resp.status_code == 200:
            class_info = resp.json()
            await call.message.answer(f"Ты присоединился к классу {class_info['class_name']}")
        else:
            await call.message.answer(f"Произошла ошибка: {resp.status_code}, {resp.text}")
    except Exception as e:
        logging.error(f"Error joining class: {str(e)}")
        await call.message.answer("Произошла ошибка при присоединении к классу. Попробуйте позже.")