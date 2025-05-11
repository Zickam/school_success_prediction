from typing import Dict, List
from app.db.schemas.user import Roles

def get_role_menu(role: Roles) -> Dict[str, List[Dict[str, str]]]:
    """Get menu keyboard based on user role"""
    menu_map = {
        Roles.principal: [
            [{"text": "📊 Панель управления", "callback_data": "dashboard"}],
            [{"text": "👥 Классы", "callback_data": "classes"}],
            [{"text": "👨‍🏫 Учителя", "callback_data": "teachers"}],
            [{"text": "📈 Статистика", "callback_data": "statistics"}]
        ],
        Roles.deputy_principal: [
            [{"text": "📊 Панель управления", "callback_data": "dashboard"}],
            [{"text": "👥 Классы", "callback_data": "classes"}],
            [{"text": "👨‍🏫 Учителя", "callback_data": "teachers"}],
            [{"text": "📈 Статистика", "callback_data": "statistics"}]
        ],
        Roles.homeroom_teacher: [
            [{"text": "👥 Мой класс", "callback_data": "my_class"}],
            [{"text": "📊 Оценки", "callback_data": "grades"}],
            [{"text": "📈 Статистика", "callback_data": "statistics"}]
        ],
        Roles.subject_teacher: [
            [{"text": "📚 Мои предметы", "callback_data": "my_subjects"}],
            [{"text": "📊 Оценки", "callback_data": "grades"}],
            [{"text": "📈 Статистика", "callback_data": "statistics"}]
        ],
        Roles.student: [
            [{"text": "📊 Мои оценки", "callback_data": "my_grades"}],
            [{"text": "📈 Статистика", "callback_data": "statistics"}]
        ],
        Roles.parent: [
            [{"text": "👶 Мои дети", "callback_data": "my_children"}],
            [{"text": "📊 Оценки", "callback_data": "grades"}],
            [{"text": "📈 Статистика", "callback_data": "statistics"}]
        ]
    }
    
    return {"inline_keyboard": menu_map.get(role, [])}

def get_role_welcome_message(role: Roles, name: str) -> str:
    """Get welcome message based on user role"""
    welcome_map = {
        Roles.principal: f"Добро пожаловать, Директор {name}!",
        Roles.deputy_principal: f"Добро пожаловать, Заместитель директора {name}!",
        Roles.homeroom_teacher: f"Добро пожаловать, Учитель {name}!",
        Roles.subject_teacher: f"Добро пожаловать, Учитель {name}!",
        Roles.student: f"Добро пожаловать, {name}!",
        Roles.parent: f"Добро пожаловать, {name}!"
    }
    
    return welcome_map.get(role, f"Добро пожаловать, {name}!")

def get_role_error_message(role: Roles, action: str) -> str:
    """Get error message for unauthorized actions"""
    return f"Извините, {role.value} не может получить доступ к {action}." 