from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.schemas.user import Roles

def keyboardChooseRole():
    keyboard = InlineKeyboardBuilder()
    
    # Group roles by type
    student_roles = [
        (Roles.student, "👨‍🎓 Ученик"),
        (Roles.parent, "👨‍👩‍👧‍👦 Родитель")
    ]
    
    teacher_roles = [
        (Roles.homeroom_teacher, "👨‍🏫 Классный руководитель"),
        (Roles.subject_teacher, "📚 Учитель-предметник")
    ]
    
    admin_roles = [
        (Roles.deputy_principal, "👨‍💼 Завуч"),
        (Roles.principal, "👨‍💼 Директор")
    ]
    
    # Add role buttons with emojis
    for role, label in student_roles + teacher_roles + admin_roles:
        keyboard.add(InlineKeyboardButton(text=label, callback_data=f"role|{role}"))
    
    return keyboard.as_markup()

def keyboardAcceptInvite(class_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text="✅ Принять", callback_data=f"join|{class_id}"))
    keyboard.add(InlineKeyboardButton(text="❌ Отклонить", callback_data="menu"))

    return keyboard.as_markup()