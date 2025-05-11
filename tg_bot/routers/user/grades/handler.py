from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from tg_bot.core.config import settings
import aiohttp

router = Router()

class GradeStates(StatesGroup):
    waiting_for_grade = State()
    waiting_for_subject = State()

@router.message(Command("grades"))
async def get_grades(message: types.Message):
    """Get user's grades"""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{settings.API_URL}/grades",
            params={"user_uuid": message.from_user.id}
        ) as response:
            if response.status == 200:
                grades = await response.json()
                if not grades:
                    await message.answer("У вас пока нет оценок.")
                    return

                # Format grades
                grade_text = "Ваши оценки:\n\n"
                for grade in grades:
                    grade_text += f"Предмет: {grade['subject_name']}\n"
                    grade_text += f"Оценка: {grade['value']}\n"
                    grade_text += f"Дата: {grade['created_at']}\n\n"

                await message.answer(grade_text)
            else:
                await message.answer("Не удалось получить оценки. Попробуйте позже.")

@router.message(Command("add_grade"))
async def add_grade_start(message: types.Message, state: FSMContext):
    """Start adding a new grade"""
    await state.set_state(GradeStates.waiting_for_subject)
    await message.answer("Введите название предмета:")

@router.message(GradeStates.waiting_for_subject)
async def process_subject(message: types.Message, state: FSMContext):
    """Process subject name and ask for grade"""
    await state.update_data(subject=message.text)
    await state.set_state(GradeStates.waiting_for_grade)
    await message.answer("Введите оценку (от 1 до 5):")

@router.message(GradeStates.waiting_for_grade)
async def process_grade(message: types.Message, state: FSMContext):
    """Process grade value and save it"""
    try:
        grade = float(message.text)
        if not 1 <= grade <= 5:
            await message.answer("Оценка должна быть от 1 до 5. Попробуйте снова:")
            return

        data = await state.get_data()
        subject = data["subject"]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.API_URL}/grades",
                json={
                    "user_uuid": message.from_user.id,
                    "subject": subject,
                    "value": grade
                }
            ) as response:
                if response.status == 201:
                    await message.answer("Оценка успешно добавлена!")
                else:
                    await message.answer("Не удалось добавить оценку. Попробуйте позже.")

        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число от 1 до 5:") 