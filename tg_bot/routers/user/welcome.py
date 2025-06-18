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


async def getClassDescription(_class_resp: dict) -> str:
    _school_resp = (await httpx_client.get("school", params={"uuid": _class_resp["school_uuid"]})).json()
    return f"Школа: {_school_resp['facility_name']}\n" + f"Класс: {_class_resp['class_name']}\n" + f"Начало обучения: {_class_resp['start_year']}\n"


@router.message(Command("start"))
@updateUserDecorator
async def start(msg: Message, state: FSMContext):
    user_class = await httpx_client.get("user/class", params={"chat_id": msg.chat.id})
    if user_class.status_code == 200:
        class_description = await getClassDescription(user_class.json())
        text = "Ты состоишь в классе:\n\n" + class_description
        await msg.answer(text)
        return

    class_uuid_to_join = msg.text.replace("/start", "").strip()
    if not class_uuid_to_join:
        await msg.answer("Привет! Это бот для оценки успехов школьников. Обратись к своему учителю для получения приглашения в класс!")
        return

    class_resp = await httpx_client.get("class", params={"uuid": class_uuid_to_join})
    if class_resp.status_code == 200:
        class_resp = class_resp.json()
        class_description = await getClassDescription(class_resp)

        text = f"Привет! Это бот для оценки успехов школьников. Тебя пригласили в класс.\n\n" + class_description
        await msg.answer(
            text,
            reply_markup=keyboards.user.welcome.keyboardAcceptInvite(class_uuid_to_join)
        )
    else:
        logging.info(f"start function {class_resp.status_code} {class_resp.text}")
        await msg.answer(f"Привет! Это бот для оценки успехов школьников. Скорее всего с твоей ссылкой для приглашения в класс что-то не так, обратись к учителю за получением новой")


@router.callback_query(F.data.startswith("join|"))
@updateUserDecorator
async def joinClass(call: CallbackQuery, state: FSMContext):
    class_uuid = call.data.replace("join|", "")
    data = (await state.get_data())
    logging.info(data)
    resp = await httpx_client.post("class/student_join", params={"user_uuid": data["user_uuid"],
                                                                 "class_uuid": class_uuid})
    if resp.status_code == 409:
        await call.message.answer(f"Ты уже состоишь в этом классе")
    elif resp.status_code == 200:
        class_description = await getClassDescription(resp.json())
        await call.message.answer(f"Ты присоединился к классу\n\n{class_description}")
    else:
        await call.message.answer(f"Произошла ошибка: {resp.status_code, resp.text}")


@router.message(Command("my_grades"))
@updateUserDecorator
async def showMyGrades(msg: Message, state: FSMContext):
    resp = await httpx_client.get("mark", params={"chat_id": msg.chat.id})
    resp = resp.json()

    marks = {}
    for mark in resp:
        discipline = mark["discipline"]
        if discipline not in marks:
            marks[discipline] = []

        marks[discipline].append(mark["mark"])

    message = "Твои оценки:\n\n"
    for discipline, _marks in marks.items():
        message += discipline + ": " + str(_marks)[1:-1] + "\n"

    await msg.answer(message)


@router.message()
@updateUserDecorator
async def showMenu(msg: Message, state: FSMContext):
    await msg.answer("Привет! Это бот для оценки успехов школьников. Обратись к своему учителю для получения приглашения в класс!")

@router.callback_query(F.data == "menu")
@updateUserDecorator
async def showMenuCQ(call: CallbackQuery, state: FSMContext):
    await showMenu(call.message, state)
