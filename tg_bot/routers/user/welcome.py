import logging
from uuid import UUID

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from tg_bot.filters import IsPrivate, IsPrivateCallback
from tg_bot import keyboards
from tg_bot.config import httpx_client
from tg_bot.common import updateUserDecorator
from app.db.schemas.user import Roles
from app.telegram.menu import get_role_menu, get_role_welcome_message, get_role_error_message

router = Router()
router.message.filter(IsPrivate())
router.callback_query.filter(IsPrivateCallback())

async def get_user_classes(user_uuid: str) -> list:
    """Get all classes for a user"""
    resp = await httpx_client.get(f"school/classes/user/{user_uuid}")
    if resp.status_code == 200:
        return resp.json()
    return []

async def get_class_details(class_uuid: str) -> dict:
    """Get detailed information about a class"""
    resp = await httpx_client.get(f"school/class/{class_uuid}")
    if resp.status_code == 200:
        return resp.json()
    return {}

async def get_class_teachers(class_uuid: str) -> list:
    """Get all teachers in a class"""
    resp = await httpx_client.get(f"school/class/{class_uuid}/teachers")
    if resp.status_code == 200:
        return resp.json()
    return []

async def get_class_students(class_uuid: str) -> list:
    """Get all students in a class"""
    resp = await httpx_client.get(f"school/class/{class_uuid}/students")
    if resp.status_code == 200:
        return resp.json()
    return []

@router.message(CommandStart())
async def start(message: Message):
    """Handle /start command with role-based menu"""
    # Get or create user
    chat_id = message.chat.id
    resp = await httpx_client.get(f"user?chat_id={chat_id}")
    
    if resp.status_code == 404:
        # Create new user with student role by default
        user_data = {
            "chat_id": chat_id,
            "name": message.from_user.full_name,
            "role": Roles.student
        }
        resp = await httpx_client.post("user", json=user_data)
        if resp.status_code != 200:
            await message.answer("Error creating user. Please try again later.")
            return
        user = resp.json()
    else:
        user = resp.json()

    # Send welcome message with role-specific menu
    welcome_message = get_role_welcome_message(user["role"], user["name"])
    menu = get_role_menu(user["role"])
    
    await message.answer(
        text=welcome_message,
        reply_markup=menu
    )

@router.callback_query(F.data == "dashboard")
async def dashboard(callback: CallbackQuery):
    """Show school dashboard (admin only)"""
    # Get user
    resp = await httpx_client.get(f"user?chat_id={callback.message.chat.id}")
    if resp.status_code != 200:
        await callback.answer("User not found", show_alert=True)
        return
    
    user = resp.json()
    if user["role"] not in [Roles.principal, Roles.deputy_principal]:
        await callback.answer("You don't have permission to view the dashboard", show_alert=True)
        return

    # Get school stats
    resp = await httpx_client.get("school/stats")
    if resp.status_code != 200:
        await callback.answer("Error fetching school stats", show_alert=True)
        return
    
    stats = resp.json()
    message = (
        f"🏫 School Dashboard\n\n"
        f"School: {stats['school_name']}\n"
        f"Classes: {stats['class_count']}\n"
        f"Teachers: {stats['teacher_count']}\n"
    )

    await callback.message.edit_text(
        text=message,
        reply_markup=get_role_menu(user["role"])
    )

@router.callback_query(F.data == "my_class")
async def my_class(callback: CallbackQuery):
    """Show homeroom teacher's class"""
    # Get user
    resp = await httpx_client.get(f"user?chat_id={callback.message.chat.id}")
    if resp.status_code != 200:
        await callback.answer("User not found", show_alert=True)
        return
    
    user = resp.json()
    if user["role"] != Roles.homeroom_teacher:
        await callback.answer("You don't have permission to view this class", show_alert=True)
        return

    # Get teacher's class
    resp = await httpx_client.get(f"school/class/teacher/{user['uuid']}")
    if resp.status_code != 200:
        await callback.answer("No class assigned", show_alert=True)
        return
    
    class_data = resp.json()
    
    # Get students in class
    resp = await httpx_client.get(f"school/class/{class_data['uuid']}/students")
    if resp.status_code != 200:
        await callback.answer("Error fetching students", show_alert=True)
        return
    
    students = resp.json()

    # Format class message
    message = (
        f"👥 Class: {class_data['name']}\n\n"
        f"Students ({len(students)}):\n"
    )
    for student in students:
        message += f"- {student['name']}\n"

    await callback.message.edit_text(
        text=message,
        reply_markup=get_role_menu(user["role"])
    )

@router.callback_query(F.data == "my_subjects")
async def my_subjects(callback: CallbackQuery):
    """Show subject teacher's subjects"""
    # Get user
    resp = await httpx_client.get(f"user?chat_id={callback.message.chat.id}")
    if resp.status_code != 200:
        await callback.answer("User not found", show_alert=True)
        return
    
    user = resp.json()
    if user["role"] != Roles.subject_teacher:
        await callback.answer("You don't have permission to view these subjects", show_alert=True)
        return

    # Get teacher's subjects
    resp = await httpx_client.get(f"school/subject/teacher/{user['uuid']}")
    if resp.status_code != 200:
        await callback.answer("No subjects assigned", show_alert=True)
        return
    
    subjects = resp.json()

    # Format subjects message
    message = "📚 Your Subjects:\n\n"
    for subject in subjects:
        message += f"- {subject['name']}\n"

    await callback.message.edit_text(
        text=message,
        reply_markup=get_role_menu(user["role"])
    )

@router.callback_query(F.data == "view_grades")
async def view_grades(callback: CallbackQuery):
    """View grades with access control"""
    # Get user
    resp = await httpx_client.get(f"user?chat_id={callback.message.chat.id}")
    if resp.status_code != 200:
        await callback.answer("User not found", show_alert=True)
        return
    
    user = resp.json()

    # Get grades based on role
    resp = await httpx_client.get(f"school/grade/user/{user['uuid']}")
    if resp.status_code != 200:
        await callback.answer("No grades found", show_alert=True)
        return
    
    grades = resp.json()

    # Format grades message
    message = "📊 Grades:\n\n"
    for grade in grades:
        message += f"- {grade['value']} in {grade['subject_name']} ({grade['date']})\n"

    await callback.message.edit_text(
        text=message,
        reply_markup=get_role_menu(user["role"])
    )

@router.callback_query(F.data == "my_children")
async def my_children(callback: CallbackQuery):
    """Show parent's children"""
    # Get user
    resp = await httpx_client.get(f"user?chat_id={callback.message.chat.id}")
    if resp.status_code != 200:
        await callback.answer("User not found", show_alert=True)
        return
    
    user = resp.json()
    if user["role"] != Roles.parent:
        await callback.answer("You don't have permission to view children", show_alert=True)
        return

    # Get children
    resp = await httpx_client.get(f"user/{user['uuid']}/children")
    if resp.status_code != 200:
        await callback.answer("No children assigned", show_alert=True)
        return
    
    children = resp.json()

    # Format children message
    message = "👶 Your Children:\n\n"
    for child in children:
        message += f"- {child['name']}\n"

    await callback.message.edit_text(
        text=message,
        reply_markup=get_role_menu(user["role"])
    )

@router.callback_query(F.data == "my_grades")
async def my_grades(callback: CallbackQuery):
    """Show student's own grades"""
    # Get user
    resp = await httpx_client.get(f"user?chat_id={callback.message.chat.id}")
    if resp.status_code != 200:
        await callback.answer("User not found", show_alert=True)
        return
    
    user = resp.json()
    if user["role"] != Roles.student:
        await callback.answer("You don't have permission to view these grades", show_alert=True)
        return

    # Get student's grades
    resp = await httpx_client.get(f"school/grade/student/{user['uuid']}")
    if resp.status_code != 200:
        await callback.answer("No grades found", show_alert=True)
        return
    
    grades = resp.json()

    # Format grades message
    message = "📊 Your Grades:\n\n"
    for grade in grades:
        message += f"- {grade['value']} in {grade['subject_name']} ({grade['date']})\n"

    await callback.message.edit_text(
        text=message,
        reply_markup=get_role_menu(user["role"])
    )

@router.callback_query(F.data == "settings")
async def settings(callback: CallbackQuery):
    """Show settings menu"""
    # Get user
    resp = await httpx_client.get(f"user?chat_id={callback.message.chat.id}")
    if resp.status_code != 200:
        await callback.answer("User not found", show_alert=True)
        return
    
    user = resp.json()
    
    # Create settings menu based on role
    settings_menu = get_role_menu(user["role"])
    
    await callback.message.edit_text(
        text="⚙️ Settings",
        reply_markup=settings_menu
    )