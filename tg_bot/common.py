from functools import wraps
from typing import Callable
import logging

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardMarkup

from app.db.schemas.user import Roles

async def getFSMContext(user_id: int) -> FSMContext:
    from tg_bot.config import dp, bot

    return FSMContext(
        storage=dp.storage,  # dp - экземпляр диспатчера
        key=StorageKey(
            chat_id=user_id,  # если юзер в ЛС, то chat_id=user_id
            user_id=user_id,
            bot_id=bot.id,
        ),
    )

async def updateNewUser(msg: Message):
    from tg_bot.config import httpx_client

    params = {
        "chat_id": msg.chat.id,
        "role": Roles.student.value
    }

    resp = await httpx_client.post(
        "user",
        params=params
    )
    state = await getFSMContext(msg.chat.id)
    await state.update_data({"user_uuid": resp.json()["uuid"]})


async def updateExistingUser(msg: Message):
    from tg_bot.config import httpx_client

    # await httpx_client.patch(
    #     "user",
    #     params={"chat_id": msg.chat.id},
    # )
    params = {
        "chat_id": msg.chat.id,
    }
    resp = await httpx_client.get(
        "user",
        params=params
    )

    state = await getFSMContext(msg.chat.id)
    await state.update_data({"user_uuid": resp.json()["uuid"]})


async def isUserExist(msg: Message) -> bool:
    from tg_bot.config import httpx_client

    resp = await httpx_client.get("user", params={"chat_id": msg.chat.id})
    return resp.status_code == 200


def getTypeMessage(_input: Message | CallbackQuery) -> Message:
    if isinstance(_input, CallbackQuery):
        return _input.message
    else:
        return _input


def updateUserDecorator(func: Callable):
    @wraps(func)
    async def wrapper(_input: Message | CallbackQuery, state: FSMContext):
        msg = getTypeMessage(_input)

        logging.info("UPDATE USER DECORATOR")
        if await isUserExist(msg):
            logging.info("ISUSEREXIST")
            await updateExistingUser(msg)
            await func(_input, state)
        else:
            logging.info("NOT ISUSEREXIST")
            await updateNewUser(msg)
            await func(_input, state)

    return wrapper
