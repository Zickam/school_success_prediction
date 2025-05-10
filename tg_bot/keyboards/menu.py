from typing import Dict, List
from app.db.schemas.user import Roles

def get_role_menu(role: Roles) -> Dict[str, List[Dict[str, str]]]:
    """Get menu keyboard based on user role"""
    menu_map = {
        Roles.principal: [
            [{"text": "📊 Dashboard", "callback_data": "dashboard"}],
            [{"text": "👥 Classes", "callback_data": "classes"}],
            [{"text": "👨‍🏫 Teachers", "callback_data": "teachers"}],
            [{"text": "📈 Statistics", "callback_data": "statistics"}]
        ],
        Roles.deputy_principal: [
            [{"text": "📊 Dashboard", "callback_data": "dashboard"}],
            [{"text": "👥 Classes", "callback_data": "classes"}],
            [{"text": "👨‍🏫 Teachers", "callback_data": "teachers"}],
            [{"text": "📈 Statistics", "callback_data": "statistics"}]
        ],
        Roles.homeroom_teacher: [
            [{"text": "👥 My Class", "callback_data": "my_class"}],
            [{"text": "📊 Grades", "callback_data": "grades"}],
            [{"text": "📈 Statistics", "callback_data": "statistics"}]
        ],
        Roles.subject_teacher: [
            [{"text": "📚 My Subjects", "callback_data": "my_subjects"}],
            [{"text": "📊 Grades", "callback_data": "grades"}],
            [{"text": "📈 Statistics", "callback_data": "statistics"}]
        ],
        Roles.student: [
            [{"text": "📊 My Grades", "callback_data": "my_grades"}],
            [{"text": "📈 Statistics", "callback_data": "statistics"}]
        ],
        Roles.parent: [
            [{"text": "👶 My Children", "callback_data": "my_children"}],
            [{"text": "📊 Grades", "callback_data": "grades"}],
            [{"text": "📈 Statistics", "callback_data": "statistics"}]
        ]
    }
    
    return {"inline_keyboard": menu_map.get(role, [])}

def get_role_welcome_message(role: Roles, name: str) -> str:
    """Get welcome message based on user role"""
    welcome_map = {
        Roles.principal: f"Welcome back, Principal {name}!",
        Roles.deputy_principal: f"Welcome back, Deputy Principal {name}!",
        Roles.homeroom_teacher: f"Welcome back, Teacher {name}!",
        Roles.subject_teacher: f"Welcome back, Teacher {name}!",
        Roles.student: f"Welcome back, {name}!",
        Roles.parent: f"Welcome back, {name}!"
    }
    
    return welcome_map.get(role, f"Welcome back, {name}!")

def get_role_error_message(role: Roles, action: str) -> str:
    """Get error message for unauthorized actions"""
    return f"Sorry, {role.value}s cannot access {action}." 