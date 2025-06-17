from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.schemas.user import Roles


def keyboardChooseRole():
    keyboard = InlineKeyboardBuilder()

    student_roles = [
        (Roles.student, "👨‍🎓 Ученик"),
        (Roles.parent, "👨‍👩‍👧‍👦 Родитель"),
    ]

    teacher_roles = [
        (Roles.homeroom_teacher, "👨‍🏫 Классный руководитель"),
        (Roles.subject_teacher, "📚 Учитель-предметник"),
    ]

    admin_roles = [
        (Roles.deputy_principal, "👨‍💼 Завуч"),
        (Roles.principal, "👨‍💼 Директор"),
    ]

    for role, label in student_roles + teacher_roles + admin_roles:
        keyboard.add(InlineKeyboardButton(text=label, callback_data=f"role|{role}"))

    return keyboard.as_markup()


def get_role_menu(role: Roles) -> InlineKeyboardMarkup:

    if role == Roles.principal or role == Roles.deputy_principal:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard")],
                [
                    InlineKeyboardButton(
                        text="👥 Manage Users", callback_data="manage_users"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📚 Manage Classes", callback_data="manage_classes"
                    )
                ],
                [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
            ]
        )
    elif role == Roles.homeroom_teacher:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👥 My Class", callback_data="my_class")],
                [InlineKeyboardButton(text="📊 Grades", callback_data="view_grades")],
                [InlineKeyboardButton(text="📝 Reports", callback_data="reports")],
                [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
            ]
        )
    elif role == Roles.subject_teacher:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📚 My Subjects", callback_data="my_subjects"
                    )
                ],
                [InlineKeyboardButton(text="📊 Grades", callback_data="view_grades")],
                [InlineKeyboardButton(text="📝 Reports", callback_data="reports")],
                [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
            ]
        )
    elif role == Roles.parent:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👶 My Children", callback_data="my_children"
                    )
                ],
                [InlineKeyboardButton(text="📊 Grades", callback_data="view_grades")],
                [InlineKeyboardButton(text="📝 Reports", callback_data="reports")],
                [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
            ]
        )
    else:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 My Grades", callback_data="my_grades")],
                [
                    InlineKeyboardButton(
                        text="📚 My Subjects", callback_data="my_subjects"
                    )
                ],
                [InlineKeyboardButton(text="📝 Reports", callback_data="reports")],
                [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
            ]
        )
