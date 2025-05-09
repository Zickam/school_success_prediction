import logging
from uuid import UUID

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
import httpx

from tg_bot.filters import IsPrivate, IsPrivateCallback
from tg_bot import keyboards
from tg_bot.config import httpx_client
from tg_bot.common import updateUserDecorator
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

async def make_api_request(method, url, **kwargs):
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

@router.callback_query(F.data == "dashboard")
async def dashboard(callback: CallbackQuery):
    """Show dashboard for admin roles"""
    try:
        response = await make_api_request("GET", f"/user?chat_id={callback.from_user.id}")
        
        if response.status_code == 200:
            user_data = response.json()
            role = Roles(user_data["role"])
            
            if role in [Roles.principal, Roles.deputy_principal]:
                # Get school stats
                school_response = await make_api_request("GET", "/school/stats")
                if school_response.status_code == 200:
                    stats = school_response.json()
                    await callback.message.answer(
                        f"📊 School Dashboard\n\n"
                        f"Total Students: {stats['total_students']}\n"
                        f"Total Teachers: {stats['total_teachers']}\n"
                        f"Total Classes: {stats['total_classes']}\n"
                        f"Average Grade: {stats['average_grade']:.2f}"
                    )
                else:
                    await callback.message.answer("Failed to get school statistics.")
            else:
                await callback.message.answer(get_role_error_message(role, "dashboard"))
        else:
            await callback.message.answer("Failed to get user data.")
    except Exception as e:
        logger.error(f"Error in dashboard: {e}")
        await callback.message.answer(str(e))

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

@router.callback_query(F.data == "my_subjects")
async def my_subjects(callback: CallbackQuery):
    """Show subject teacher's subjects"""
    try:
        response = await make_api_request("GET", f"/user?chat_id={callback.from_user.id}")
        
        if response.status_code == 200:
            user_data = response.json()
            role = Roles(user_data["role"])
            
            if role == Roles.subject_teacher:
                subjects = user_data.get("teacher_subjects", [])
                if subjects:
                    message = "📚 Your Subjects:\n\n"
                    for subject in subjects:
                        message += f"- {subject['subject_name']}\n"
                    await callback.message.answer(message)
                else:
                    await callback.message.answer("You don't have any subjects assigned.")
            else:
                await callback.message.answer(get_role_error_message(role, "my_subjects"))
        else:
            await callback.message.answer("Failed to get user data.")
    except Exception as e:
        logger.error(f"Error in my_subjects: {e}")
        await callback.message.answer(str(e))

@router.callback_query(F.data == "my_grades")
async def my_grades(callback: CallbackQuery):
    """Show student's grades"""
    try:
        response = await make_api_request("GET", f"/user?chat_id={callback.from_user.id}")
        
        if response.status_code == 200:
            user_data = response.json()
            role = Roles(user_data["role"])
            
            if role == Roles.student:
                # Get student's grades
                grades_response = await make_api_request("GET", f"/grade/student/{user_data['uuid']}")
                if grades_response.status_code == 200:
                    grades = grades_response.json()
                    if grades:
                        message = "📊 Your Grades:\n\n"
                        for grade in grades:
                            message += f"{grade['subject_name']}: {grade['value']}\n"
                        await callback.message.answer(message)
                    else:
                        await callback.message.answer("You don't have any grades yet.")
                else:
                    await callback.message.answer("Failed to get grades.")
            else:
                await callback.message.answer(get_role_error_message(role, "my_grades"))
        else:
            await callback.message.answer("Failed to get user data.")
    except Exception as e:
        logger.error(f"Error in my_grades: {e}")
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
async def show_statistics(callback: CallbackQuery):
    """Show statistics"""
    try:
        response = await make_api_request("GET", f"/user?chat_id={callback.from_user.id}")
        
        if response.status_code == 200:
            user_data = response.json()
            role = Roles(user_data["role"])
            user_uuid = user_data["uuid"]
            
            # Get all grades for statistics
            grades_response = await make_api_request(
                "GET",
                "/grades",
                params={"student_id": user_uuid}
            )
            
            if grades_response:
                # Count grades
                grade_counts = {}
                for grade in grades_response:
                    value = grade['value']
                    grade_counts[value] = grade_counts.get(value, 0) + 1
                
                # Get attendance data
                attendance_response = await make_api_request(
                    "GET",
                    f"/attendance/student/{user_uuid}"
                )
                
                attendance_stats = {
                    "present": 0,
                    "absent": 0,
                    "late": 0
                }
                
                if attendance_response:
                    for record in attendance_response:
                        status = record['status']
                        attendance_stats[status] = attendance_stats.get(status, 0) + 1
                
                # Format statistics message
                text = "📊 Statistics\n\n"
                
                # Grade distribution
                for grade in sorted(grade_counts.keys(), reverse=True):
                    text += f"Grade {grade}: {grade_counts[grade]} times\n"
                
                # Calculate average
                if grade_counts:
                    total = sum(grade * count for grade, count in grade_counts.items())
                    count = sum(grade_counts.values())
                    average = total / count
                    text += f"\nAverage Grade: {average:.2f}\n"
                
                # Attendance statistics
                text += f"\nAbsent Days: {attendance_stats['absent']}\n"
                text += f"Late Days: {attendance_stats['late']}\n"
                
                # Calculate attendance rate
                total_days = sum(attendance_stats.values())
                if total_days > 0:
                    attendance_rate = (attendance_stats['present'] / total_days) * 100
                    text += f"Attendance Rate: {attendance_rate:.1f}%"
                
                await callback.message.answer(text)
            else:
                await callback.message.answer("❌ Failed to fetch grades")
        else:
            await callback.message.answer("Failed to get user data.")
    except Exception as e:
        logger.error(f"Error in statistics: {e}")
        await callback.message.answer(str(e))