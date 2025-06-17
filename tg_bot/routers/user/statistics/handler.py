from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from tg_bot.filters import IsPrivate
from tg_bot.keyboards.statistics import (
    get_statistics_menu_keyboard,
    get_subject_selection_keyboard,
    get_time_period_keyboard,
)
from tg_bot.api_client import make_api_request

router = Router()
router.message.filter(IsPrivate())


class StatisticsStates(StatesGroup):

    selecting_subject = State()
    selecting_time_period = State()


@router.message(Command("statistics"))
async def show_statistics_menu(message: Message):

    await message.answer(
        "📊 Меню статистики\n\n" "Выберите, что вы хотите посмотреть:",
        reply_markup=get_statistics_menu_keyboard(),
    )


@router.callback_query(F.data.startswith("stats_"))
async def handle_statistics_callback(callback: CallbackQuery, state: FSMContext):

    action = callback.data.split("_")[1]

    if action == "overall":
        response = await make_api_request(
            "GET", f"/statistics/student/{callback.from_user.id}/overall"
        )

        if response and "subjects" in response:
            text = "📊 Ваша общая статистика:\n\n"
            for subject in response["subjects"]:
                text += f"📚 {subject['name']}:\n"
                text += f"   Средний балл: {subject['average']}\n"
                text += f"   Количество оценок: {subject['count']}\n\n"
            text += f"📈 Общий средний балл: {response['overall_average']}"

            await callback.message.edit_text(text)
        else:
            await callback.message.edit_text("❌ Не удалось получить статистику")

    elif action == "progress":
        response = await make_api_request("GET", f"/subjects")

        if response:
            await state.set_state(StatisticsStates.selecting_subject)
            await callback.message.edit_text(
                "Выберите предмет для просмотра прогресса:",
                reply_markup=get_subject_selection_keyboard(response),
            )
        else:
            await callback.message.edit_text("❌ Не удалось получить список предметов")

    elif action == "class":
        response = await make_api_request(
            "GET", f"/statistics/class/{callback.from_user.id}/subject/1"
        )

        if response and "distribution" in response:
            text = "📊 Статистика класса:\n\n"
            text += f"📚 ID предмета: {response['subject_id']}\n"
            text += f"👥 Всего оценок: {response['total_grades']}\n"
            text += f"📈 Средний балл класса: {response['average']}\n\n"
            text += "Распределение оценок:\n"

            for grade in response["distribution"]:
                text += f"Оценка {grade['grade']}: {grade['count']} ({grade['percentage']}%)\n"

            await callback.message.edit_text(text)
        else:
            await callback.message.edit_text("❌ Не удалось получить статистику класса")


@router.callback_query(
    StatisticsStates.selecting_subject, F.data.startswith("subject_")
)
async def handle_subject_selection(callback: CallbackQuery, state: FSMContext):

    subject_id = int(callback.data.split("_")[1])
    await state.update_data(selected_subject=subject_id)

    await state.set_state(StatisticsStates.selecting_time_period)
    await callback.message.edit_text(
        "Select time period:", reply_markup=get_time_period_keyboard()
    )


@router.callback_query(
    StatisticsStates.selecting_time_period, F.data.startswith("period_")
)
async def handle_time_period_selection(callback: CallbackQuery, state: FSMContext):

    days = int(callback.data.split("_")[1])
    data = await state.get_data()
    subject_id = data["selected_subject"]

    response = await make_api_request(
        "GET",
        f"/statistics/student/{callback.from_user.id}/progress",
        params={"subject_id": subject_id, "days": days},
    )

    if response and "progress" in response:
        text = f"📈 Прогресс за последние {days} дней:\n\n"

        for grade in response["progress"]:
            text += f"📅 {grade['date']}\n"
            text += f"Оценка: {grade['value']}\n"
            if grade["comment"]:
                text += f"Комментарий: {grade['comment']}\n"
            text += "\n"

        await callback.message.edit_text(text)
    else:
        await callback.message.edit_text("❌ Не удалось получить данные о прогрессе")

    await state.clear()
