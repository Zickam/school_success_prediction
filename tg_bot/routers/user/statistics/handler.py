from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from tg_bot.filters import IsPrivate
from tg_bot.keyboards.statistics import (
    get_statistics_menu_keyboard,
    get_subject_selection_keyboard,
    get_time_period_keyboard
)
from tg_bot.api_client import make_api_request

router = Router()
router.message.filter(IsPrivate())

class StatisticsStates(StatesGroup):
    """States for statistics menu"""
    selecting_subject = State()
    selecting_time_period = State()

@router.message(Command("statistics"))
async def show_statistics_menu(message: Message):
    """Show statistics menu"""
    await message.answer(
        "📊 Statistics Menu\n\n"
        "Choose what you want to view:",
        reply_markup=get_statistics_menu_keyboard()
    )

@router.callback_query(F.data.startswith("stats_"))
async def handle_statistics_callback(callback: CallbackQuery, state: FSMContext):
    """Handle statistics menu callbacks"""
    action = callback.data.split("_")[1]
    
    if action == "overall":
        # Get student's overall statistics
        response = await make_api_request(
            "GET",
            f"/statistics/student/{callback.from_user.id}/overall"
        )
        
        if response and "subjects" in response:
            text = "📊 Your Overall Statistics:\n\n"
            for subject in response["subjects"]:
                text += f"📚 {subject['name']}:\n"
                text += f"   Average: {subject['average']}\n"
                text += f"   Grades: {subject['count']}\n\n"
            text += f"📈 Overall Average: {response['overall_average']}"
            
            await callback.message.edit_text(text)
        else:
            await callback.message.edit_text("❌ Failed to fetch statistics")
    
    elif action == "progress":
        # Get list of subjects for the student
        response = await make_api_request(
            "GET",
            f"/subjects"
        )
        
        if response:
            await state.set_state(StatisticsStates.selecting_subject)
            await callback.message.edit_text(
                "Select a subject to view progress:",
                reply_markup=get_subject_selection_keyboard(response)
            )
        else:
            await callback.message.edit_text("❌ Failed to fetch subjects")
    
    elif action == "class":
        # Get class statistics
        response = await make_api_request(
            "GET",
            f"/statistics/class/{callback.from_user.id}/subject/1"  # Default to first subject
        )
        
        if response and "distribution" in response:
            text = "📊 Class Statistics:\n\n"
            text += f"📚 Subject ID: {response['subject_id']}\n"
            text += f"👥 Total Grades: {response['total_grades']}\n"
            text += f"📈 Class Average: {response['average']}\n\n"
            text += "Grade Distribution:\n"
            
            for grade in response["distribution"]:
                text += f"Grade {grade['grade']}: {grade['count']} ({grade['percentage']}%)\n"
            
            await callback.message.edit_text(text)
        else:
            await callback.message.edit_text("❌ Failed to fetch class statistics")

@router.callback_query(StatisticsStates.selecting_subject, F.data.startswith("subject_"))
async def handle_subject_selection(callback: CallbackQuery, state: FSMContext):
    """Handle subject selection for progress view"""
    subject_id = int(callback.data.split("_")[1])
    await state.update_data(selected_subject=subject_id)
    
    await state.set_state(StatisticsStates.selecting_time_period)
    await callback.message.edit_text(
        "Select time period:",
        reply_markup=get_time_period_keyboard()
    )

@router.callback_query(StatisticsStates.selecting_time_period, F.data.startswith("period_"))
async def handle_time_period_selection(callback: CallbackQuery, state: FSMContext):
    """Handle time period selection for progress view"""
    days = int(callback.data.split("_")[1])
    data = await state.get_data()
    subject_id = data["selected_subject"]
    
    response = await make_api_request(
        "GET",
        f"/statistics/student/{callback.from_user.id}/progress",
        params={"subject_id": subject_id, "days": days}
    )
    
    if response and "progress" in response:
        text = f"📈 Progress for the last {days} days:\n\n"
        
        for grade in response["progress"]:
            text += f"📅 {grade['date']}\n"
            text += f"Grade: {grade['value']}\n"
            if grade['comment']:
                text += f"Comment: {grade['comment']}\n"
            text += "\n"
        
        await callback.message.edit_text(text)
    else:
        await callback.message.edit_text("❌ Failed to fetch progress data")
    
    await state.clear() 