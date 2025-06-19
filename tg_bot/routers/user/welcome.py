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
    return f"{_school_resp['facility_name']}\n" + f"Класс: {_class_resp['class_name']}\n"


@router.message(Command("start"))
@updateUserDecorator
async def start(msg: Message, state: FSMContext):
    try:
        # Получаем пользователя
        user_resp = await httpx_client.get("user", params={"chat_id": msg.chat.id})
        if user_resp.status_code != 200:
            raise Exception("User not found")
        user = user_resp.json()
        user_name = user.get("name", "Пользователь")

        # Проверяем, есть ли пользователь в классе
        user_class_resp = await httpx_client.get("user/class", params={"chat_id": msg.chat.id})
        if user_class_resp.status_code == 200:
            class_description = await getClassDescription(user_class_resp.json())

            text = (
                f"👋 <b>Привет, {user_name}!</b>\n\n"
                f"Ты уже присоединился к классу:\n\n"
                f"{class_description}"
            )
            await msg.answer(text, parse_mode="HTML")
            return

        # Пользователь не в классе — проверяем ссылку
        class_uuid_to_join = msg.text.replace("/start", "").strip()
        if not class_uuid_to_join:
            await msg.answer(
                f"👋 <b>Привет, {user_name}!</b>\n\n"
                f"Это бот для оценки успехов школьников.\n"
                f"Попроси у своего учителя ссылку на приглашение в класс 🏫",
                parse_mode="HTML"
            )
            return

        class_resp = await httpx_client.get("class", params={"uuid": class_uuid_to_join})
        if class_resp.status_code == 200:
            class_info = class_resp.json()
            class_description = await getClassDescription(class_info)

            text = (
                f"👋 <b>Привет, {user_name}!</b>\n\n"
                f"Тебя пригласили присоединиться к следующему классу:\n\n"
                f"{class_description}"
            )
            await msg.answer(
                text,
                reply_markup=keyboards.user.welcome.keyboardAcceptInvite(class_uuid_to_join),
                parse_mode="HTML"
            )
        else:
            logging.warning(f"Invalid invite link: {class_resp.status_code} {class_resp.text}")
            await msg.answer(
                f"⚠️ <b>Ошибка!</b>\n\n"
                f"Ссылка на класс недействительна. Попроси у учителя новую ссылку.",
                parse_mode="HTML"
            )

    except Exception as e:
        logging.exception("Ошибка в обработке команды /start")
        await msg.answer("Произошла ошибка при старте. Попробуй позже.")


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

        absences = {
            "Пропуск по уважительной причине",
            "Пропуск без уважительной причины",
            "Пропуск по болезни"
        }

        subject_data = {}
        for mark in marks:
            subject = mark["discipline"]
            value = mark["mark"]
            subject_data.setdefault(subject, []).append(value)

        # Отдельные списки
        academic_lines = []
        absence_lines = []

        for subject, values in subject_data.items():
            if subject in absences:
                absence_lines.append((subject, len(values)))
            else:
                avg = sum(values) / len(values)
                academic_lines.append((subject, avg))

        # Сортировка для стабильности вывода
        academic_lines.sort()
        absence_order = [
            "Пропуск без уважительной причины",
            "Пропуск по болезни",
            "Пропуск по уважительной причине"
        ]
        absence_lines.sort(key=lambda x: absence_order.index(x[0]) if x[0] in absence_order else 999)

        # Формирование текста
        message = "📚 <b>Твоя успеваемость:</b>\n\n"
        for subject, avg in academic_lines:
            message += f"• <b>{subject}</b>: средняя оценка {avg:.2f}\n"

        if absence_lines:
            message += "\n"
            for subject, count in absence_lines:
                message += f"• <b>{subject}</b>: {count} пропуск(ов)\n"

        await msg.answer(message, parse_mode="HTML")

        # 📈 График обычных оценок
        chart_resp = await httpx_client.get("user/plot_subject_averages", params={"chat_id": msg.chat.id})
        if chart_resp.status_code == 200:
            buf = BytesIO(chart_resp.content)
            buf.name = "grades.png"
            await msg.answer_photo(
                photo=BufferedInputFile(buf.read(), filename="grades.png"),
                caption="📊 Средние оценки по предметам"
            )
        else:
            await msg.answer("Не удалось построить график оценок.")

        # 📉 График пропусков
        absences_resp = await httpx_client.get("user/plot_absences", params={"chat_id": msg.chat.id})
        if absences_resp.status_code == 200:
            buf = BytesIO(absences_resp.content)
            buf.name = "absences.png"
            await msg.answer_photo(
                photo=BufferedInputFile(buf.read(), filename="absences.png"),
                caption="📉 Пропуски по месяцам"
            )
        else:
            await msg.answer("Не удалось построить график пропусков.")

    except Exception as e:
        await msg.answer("Произошла ошибка при получении данных.")
        raise e




@router.message(Command("statistics"))
@updateUserDecorator
async def showStatistics(msg: Message, state: FSMContext):
    # Текстовая статистика
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
        school_resp = await httpx_client.get("/school", params={"uuid": item["school_uuid"]})
        if school_resp.status_code == 200:
            school_name = school_resp.json()["facility_name"]
        else:
            school_name = "Неизвестная школа"

        message += f"<b>{school_name}</b>\n"
        message += f"Класс: {item['class_name']} ({item['start_year']} г.)\n"

        if not item["disciplines"] and not item.get("absences"):
            message += "   — нет оценок\n\n"
            continue

        # Дисциплины с оценками
        for disc in item["disciplines"]:
            message += f"   • {disc['discipline']}: ср. балл {disc['average_mark']} (всего {disc['marks_count']})\n"

        # Пропуски — отдельно
        if item.get("absences"):
            message += "\n"
            for ab in item["absences"]:
                message += f"   • {ab['discipline']}: {ab['absences_count']} пропуск(ов)\n"

        message += "\n"

    await msg.answer(message, parse_mode="HTML")

    # Пироговые диаграммы
    distribution_resp = await httpx_client.get("/teacher/plot_avg_distribution")
    if distribution_resp.status_code == 200:
        buf = BytesIO(distribution_resp.content)
        buf.name = "distribution.png"
        await msg.answer_photo(
            photo=BufferedInputFile(buf.read(), filename="distribution.png"),
            caption="📈 Распределение учеников по среднему баллу"
        )
    else:
        await msg.answer("Не удалось получить график распределения по классам.")



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
        if plot_resp.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(plot_resp.content)
                tmp_path = tmp.name

            await msg.answer_photo(photo=FSInputFile(tmp_path), caption="📊 График твоего прогресса по предметам")
        else:
            await msg.answer("Не удалось получить график прогресса.")

        # 📈 Накопленный прогресс — график
        accumulated_resp = await httpx_client.get("/user/plot_accumulated", params={"chat_id": msg.chat.id})
        if accumulated_resp.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(accumulated_resp.content)
                tmp_path = tmp.name

            await msg.answer_photo(photo=FSInputFile(tmp_path), caption="📈 Накопленный средний балл по предметам")
        else:
            await msg.answer("Не удалось получить график накопленного прогресса.")

    except Exception as e:
        await msg.answer("Произошла ошибка при получении данных.")
        raise e



@router.message()
@updateUserDecorator
async def showMenu(msg: Message, state: FSMContext):
    await start(msg, state)
    # await msg.answer("Привет! Это бот для оценки успехов школьников. Обратись к своему учителю для получения приглашения в класс!")

@router.callback_query(F.data == "menu")
@updateUserDecorator
async def showMenuCQ(call: CallbackQuery, state: FSMContext):
    # await showMenu(call.message, state)
    await start(call.message, state)

