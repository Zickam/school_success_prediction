import logging
from uuid import UUID

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
import httpx

from tg_bot.filters import IsPrivate, IsPrivateCallback
from tg_bot import keyboards
from tg_bot.config import httpx_client
from tg_bot.user_management import updateUserDecorator
from app.db.schemas.user import Roles
from tg_bot.keyboards.menu import get_role_menu, get_role_welcome_message, get_role_error_message
from tg_bot.keyboards.grades import get_grades_menu_keyboard

# Configure logger
logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsPrivate())
router.callback_query.filter(IsPrivateCallback())

class UserStates(StatesGroup):
    """User states"""
    waiting_for_name = State()
    waiting_for_role = State()

async def make_api_request(method: str, url: str, **kwargs) -> httpx.Response:
    """Make API request with error handling"""
    try:
        response = await httpx_client.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    except httpx.ConnectError as e:
        logger.error(f"Connection error: {e}")
        raise Exception("Could not connect to the server. Please try again later.")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e}")
        raise Exception(f"Server error: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise Exception("An error occurred while making the request. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise Exception("An unexpected error occurred. Please try again later.")

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    """Handle /start command"""
    try:
        # Check if user exists
        try:
            response = await make_api_request("GET", f"/user?chat_id={message.from_user.id}")
            # User exists, show role-specific menu
            user_data = response.json()
            role = Roles(user_data["role"])
            name = user_data["name"]
            
            await message.answer(
                get_role_welcome_message(role, name),
                reply_markup=get_role_menu(role)
            )
        except Exception as e:
            if "404" in str(e):
                # User doesn't exist, start registration
                await state.set_state(UserStates.waiting_for_name)
                await message.answer("Welcome! Please enter your name:")
            else:
                raise e
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer(str(e))

@router.message(UserStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Process user's name"""
    await state.update_data(name=message.text)
    await state.set_state(UserStates.waiting_for_role)
    
    # Create keyboard for role selection
    keyboard = [
        [{"text": "👨‍🏫 Teacher", "callback_data": "role_teacher"}],
        [{"text": "👨‍👩‍👧‍👦 Parent", "callback_data": "role_parent"}],
        [{"text": "👨‍🎓 Student", "callback_data": "role_student"}]
    ]
    
    await message.answer("Please select your role:", reply_markup={"inline_keyboard": keyboard})

@router.callback_query(F.data.startswith("role_"))
async def process_role(callback: CallbackQuery, state: FSMContext):
    """Process user's role selection"""
    try:
        role_map = {
            "role_teacher": Roles.subject_teacher,
            "role_parent": Roles.parent,
            "role_student": Roles.student
        }
        
        role = role_map[callback.data]
        user_data = await state.get_data()
        
        # Create user
        response = await make_api_request(
            "POST",
            "/user",
            json={
                "chat_id": callback.from_user.id,
                "name": user_data["name"],
                "role": role.value
            }
        )
        
        if response.status_code == 200:
            await callback.message.answer(
                get_role_welcome_message(role, user_data["name"]),
                reply_markup=get_role_menu(role)
            )
        else:
            await callback.message.answer("Sorry, something went wrong. Please try again later.")
    except Exception as e:
        logger.error(f"Error in process_role: {e}")
        await callback.message.answer(str(e))
    finally:
        await state.clear()

@router.callback_query(F.data == "my_class")
async def my_class(callback: CallbackQuery):
    """Show homeroom teacher's class"""
    try:
        response = await make_api_request("GET", f"/user?chat_id={callback.from_user.id}")
        
        if response.status_code == 200:
            user_data = response.json()
            role = Roles(user_data["role"])
            
            if role == Roles.homeroom_teacher:
                # Get class details
                class_response = await make_api_request("GET", f"/class/teacher/{user_data['uuid']}")
                if class_response.status_code == 200:
                    class_data = class_response.json()
                    students = class_data["students"]
                    
                    message = f"👥 Class {class_data['name']}\n\nStudents:\n"
                    for student in students:
                        message += f"- {student['name']}\n"
                    
                    await callback.message.answer(message)
                else:
                    await callback.message.answer("Failed to get class details.")
            else:
                await callback.message.answer(get_role_error_message(role, "my_class"))
        else:
            await callback.message.answer("Failed to get user data.")
    except Exception as e:
        logger.error(f"Error in my_class: {e}")
        await callback.message.answer(str(e))

@router.callback_query(F.data == "my_children")
async def my_children(callback: CallbackQuery):
    """Show parent's children"""
    try:
        response = await make_api_request("GET", f"/user?chat_id={callback.from_user.id}")
        
        if response.status_code == 200:
            user_data = response.json()
            role = Roles(user_data["role"])
            
            if role == Roles.parent:
                children = user_data.get("parent_children", [])
                if children:
                    message = "👶 Your Children:\n\n"
                    for child in children:
                        message += f"- {child['child_name']}\n"
                    await callback.message.answer(message)
                else:
                    await callback.message.answer("You don't have any children registered.")
            else:
                await callback.message.answer(get_role_error_message(role, "my_children"))
        else:
            await callback.message.answer("Failed to get user data.")
    except Exception as e:
        logger.error(f"Error in my_children: {e}")
        await callback.message.answer(str(e))

@router.callback_query(F.data == "statistics")
async def show_statistics(callback_query: CallbackQuery, bot: Bot):
    """Show user statistics"""
    try:
        # Get user data first
        user_response = await make_api_request(
            "GET",
            f"/user?chat_id={callback_query.from_user.id}"
        )
        if not user_response:
            await callback_query.message.answer(
                "❌ Failed to get user data. Please try again later."
            )
            return

        user_data = user_response.json()
        if not user_data or "uuid" not in user_data:
            await callback_query.message.answer(
                "❌ User data not found. Please try again later."
            )
            return

        # Get statistics
        stats_response = await make_api_request(
            "GET",
            f"/statistics/student/{user_data['uuid']}"
        )
        if not stats_response:
            await callback_query.message.answer(
                "❌ Failed to get statistics. Please try again later."
            )
            return

        stats_data = stats_response.json()
        
        # Format the message
        message = "📊 Your Statistics:\n\n"
        
        # Grades section
        message += "📚 Grades:\n"
        grades = stats_data["grades"]["distribution"]
        for grade, count in sorted(grades.items(), reverse=True):
            message += f"• {count} {grade} grade{'s' if count > 1 else ''}\n"
        
        if grades:
            message += f"\nAverage Grade: {stats_data['grades']['average']}\n"
        
        # Attendance section
        message += "\n📅 Attendance:\n"
        attendance = stats_data["attendance"]
        message += f"• {attendance['present_days']} days present\n"
        message += f"• {attendance['absent_days']} days absent\n"
        if attendance['late_days'] > 0:
            message += f"• {attendance['late_days']} days late\n"
        
        await callback_query.message.answer(message)
        
    except Exception as e:
        logger.error(f"Error showing statistics: {e}")
        await callback_query.message.answer(
            "❌ An error occurred while fetching statistics. Please try again later."
        )