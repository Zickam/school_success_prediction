import logging
import tempfile

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, FSInputFile
from aiogram.types import InputFile
from io import BytesIO
from aiogram.types import BufferedInputFile


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
    try:
        # Получаем оценки
        marks_resp = await httpx_client.get("mark", params={"chat_id": msg.chat.id})
        marks = marks_resp.json()

        if not marks:
            await msg.answer("У тебя пока нет оценок.")
            return

        # Составляем текст
        subject_marks = {}
        for mark in marks:
            subject = mark["discipline"]
            subject_marks.setdefault(subject, []).append(mark["mark"])

        message = "📚 <b>Твои оценки:</b>\n\n"
        for subject, grades in subject_marks.items():
            grades_str = ", ".join(str(g) for g in grades)
            message += f"<b>{subject}</b>: {grades_str}\n"

        await msg.answer(message, parse_mode="HTML")

        # Получаем график
        chart_resp = await httpx_client.get("user/plot_subject_averages", params={"chat_id": msg.chat.id})
        if chart_resp.status_code == 200:
            from io import BytesIO
            from aiogram.types import InputFile

            buf = BytesIO(chart_resp.content)
            buf.name = "grades.png"
            await msg.answer_photo(
                photo=BufferedInputFile(buf.read(), filename="grades.png"),
                caption="Средние оценки по предметам 📊"
            )
        else:
            await msg.answer("Не удалось построить график.")

    except Exception as e:
        await msg.answer("Произошла ошибка при получении данных.")
        raise e


@router.message(Command("statistics"))
@updateUserDecorator
async def showStatistics(msg: Message, state: FSMContext):
    stats_resp = await httpx_client.get("/teacher/statistics")
    if stats_resp.status_code != 200:
        await msg.answer("Произошла ошибка при получении статистики.")
        return

    stats = stats_resp.json()

    if not stats:
        await msg.answer("Пока что нет оценок.")
        return

    message = "📊 <b>Общая статистика по классам:</b>\n\n"
    for item in stats:
        # Получаем название школы
        school_resp = await httpx_client.get("/school", params={"uuid": item["school_uuid"]})
        if school_resp.status_code == 200:
            school_name = school_resp.json()["facility_name"]
        else:
            school_name = "Неизвестная школа"

        message += f"<b>{school_name}</b>\n"
        message += f"Класс: {item['class_name']} ({item['start_year']} г.)\n"

        if not item["disciplines"]:
            message += "   — нет оценок\n\n"
            continue

        for disc in item["disciplines"]:
            message += f"   • {disc['discipline']}: ср. балл {disc['average_mark']} (всего {disc['marks_count']})\n"
        message += "\n"

    await msg.answer(message, parse_mode="HTML")


@router.message(Command("analysis"))
@updateUserDecorator
async def show_prediction(msg: Message, state: FSMContext):
    try:
        # 📊 Прогноз успеваемости
        resp = await httpx_client.get("/user/predict_success", params={"chat_id": msg.chat.id})
        if resp.status_code != 200:
            await msg.answer("Не удалось получить прогноз. Попробуй позже.")
            return

        data = resp.json()

        if data.get("status") == "unknown":
            await msg.answer("У тебя пока нет оценок, поэтому прогноз невозможен.")
        else:
            emoji = {
                "успешный": "🟢",
                "неуспешный": "🔴"
            }.get(data["status"], "❓")

            text = (
                f"<b>📈 Прогноз на полугодие</b>\n\n"
                f"Статус: <b>{emoji} {data['status']}</b>\n"
                f"Уверенность: <b>{int(data['confidence'] * 100)}%</b>\n"
                f"Оценок всего: <b>{data['total_marks']}</b>\n"
                f"Троек и ниже: <b>{data['bad_marks']}</b>\n\n"
                f"{data['message']}"
            )
            await msg.answer(text, parse_mode="HTML")

        # 📈 Прогресс по неделям — график
        plot_resp = await httpx_client.get("/user/plot_progression", params={"chat_id": msg.chat.id})
        if plot_resp.status_code != 200:
            await msg.answer("Не удалось получить график прогресса.")
            return

        # сохраняем изображение временно
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(plot_resp.content)
            tmp_path = tmp.name

        await msg.answer_photo(photo=FSInputFile(tmp_path), caption="📊 График твоего прогресса по предметам")

    except Exception as e:
        await msg.answer("Произошла ошибка при получении данных.")
        raise e  # или логируй как нужно


@router.message()
@updateUserDecorator
async def showMenu(msg: Message, state: FSMContext):
    await msg.answer("Привет! Это бот для оценки успехов школьников. Обратись к своему учителю для получения приглашения в класс!")

@router.callback_query(F.data == "menu")
@updateUserDecorator
async def showMenuCQ(call: CallbackQuery, state: FSMContext):
    await showMenu(call.message, state)

