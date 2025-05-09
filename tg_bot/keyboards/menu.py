from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.db.schemas.user import Roles

def get_role_menu(role: Roles) -> InlineKeyboardMarkup:
    """Get role-specific menu"""
    if role == Roles.principal or role == Roles.deputy_principal:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard")],
            [InlineKeyboardButton(text="👥 Manage Users", callback_data="manage_users")],
            [InlineKeyboardButton(text="📚 Manage Classes", callback_data="manage_classes")],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")]
        ])
    elif role == Roles.homeroom_teacher:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 My Class", callback_data="my_class")],
            [InlineKeyboardButton(text="📊 Grades", callback_data="view_grades")],
            [InlineKeyboardButton(text="📝 Reports", callback_data="reports")],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")]
        ])
    elif role == Roles.subject_teacher:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 My Subjects", callback_data="my_subjects")],
            [InlineKeyboardButton(text="📊 Grades", callback_data="view_grades")],
            [InlineKeyboardButton(text="📝 Reports", callback_data="reports")],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")]
        ])
    elif role == Roles.parent:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👶 My Children", callback_data="my_children")],
            [InlineKeyboardButton(text="📊 Grades", callback_data="view_grades")],
            [InlineKeyboardButton(text="📝 Reports", callback_data="reports")],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")]
        ])
    else:  # student
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 My Grades", callback_data="my_grades")],
            [InlineKeyboardButton(text="📚 My Subjects", callback_data="my_subjects")],
            [InlineKeyboardButton(text="📝 Reports", callback_data="reports")],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")]
        ])

def get_role_welcome_message(role: Roles, name: str) -> str:
    """Get role-specific welcome message"""
    if role == Roles.principal or role == Roles.deputy_principal:
        return f"Welcome, {name}! 👋\n\nAs a {role.value}, you can manage the school, users, and classes."
    elif role == Roles.homeroom_teacher:
        return f"Welcome, {name}! 👋\n\nAs a homeroom teacher, you can manage your class and view grades."
    elif role == Roles.subject_teacher:
        return f"Welcome, {name}! 👋\n\nAs a subject teacher, you can manage your subjects and grades."
    elif role == Roles.parent:
        return f"Welcome, {name}! 👋\n\nAs a parent, you can view your children's grades and progress."
    else:  # student
        return f"Welcome, {name}! 👋\n\nAs a student, you can view your grades and subjects."

def get_role_error_message(role: Roles, action: str) -> str:
    """Get role-specific error message"""
    if role == Roles.principal or role == Roles.deputy_principal:
        return "You have full access to all features."
    elif role == Roles.homeroom_teacher:
        return "You can only access your class's information."
    elif role == Roles.subject_teacher:
        return "You can only access your subjects' information."
    elif role == Roles.parent:
        return "You can only access your children's information."
    else:  # student
        return "You can only access your own information." 