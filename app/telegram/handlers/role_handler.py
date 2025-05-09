from functools import wraps
from typing import List, Callable, Any, Optional
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from app.db.declaration import User
from app.db.schemas.user import Roles
from ..menu import get_role_menu, get_role_welcome_message, get_role_error_message
from ...policy import PolicyManager

class RoleHandler:
    def __init__(self, session):
        self.session = session
        self.policy = PolicyManager(session)

    async def get_user(self, message: Message | CallbackQuery) -> User:
        """Get user from database by chat_id"""
        chat_id = message.chat.id if isinstance(message, Message) else message.message.chat.id
        result = await self.session.execute(
            select(User).where(User.chat_id == chat_id)
        )
        return result.scalar_one_or_none()

    async def check_role_access(
        self,
        user: User,
        action: str,
        target_uuid: Optional[str] = None
    ) -> bool:
        """Check if user has access to perform the action"""
        if user.role in [Roles.principal, Roles.deputy_principal]:
            return True

        if action.startswith("view_"):
            if action == "view_grades":
                if user.role == Roles.student:
                    return target_uuid == str(user.uuid)
                elif user.role == Roles.parent:
                    return target_uuid in (user.parent_children or [])
                elif user.role == Roles.subject_teacher:
                    # Check if student is in teacher's subject groups
                    return await self.policy.can_view_grade(user, target_uuid)
                elif user.role == Roles.homeroom_teacher:
                    # Check if student is in teacher's class
                    return await self.policy.can_view_grade(user, target_uuid)

        elif action.startswith("manage_"):
            if action == "manage_grades":
                if user.role == Roles.subject_teacher:
                    return await self.policy.can_manage_grade(user, target_uuid)
                elif user.role == Roles.homeroom_teacher:
                    return await self.policy.can_manage_grade(user, target_uuid)

        return False

    async def handle_role_change(
        self,
        message: Message | CallbackQuery,
        user: User,
        new_role: Roles
    ) -> None:
        """Handle role change and update UI"""
        # Update user role
        user.role = new_role
        await self.session.commit()

        # Send welcome message with new role menu
        welcome_message = get_role_welcome_message(new_role, user.name)
        menu = get_role_menu(new_role)
        
        if isinstance(message, CallbackQuery):
            await message.edit_message_text(
                text=welcome_message,
                reply_markup=menu
            )
        else:
            await message.answer(
                text=welcome_message,
                reply_markup=menu
            )

    async def handle_unauthorized(
        self,
        message: Message | CallbackQuery,
        user: Optional[User],
        action: str
    ) -> None:
        """Handle unauthorized access attempts"""
        error_message = get_role_error_message(user.role if user else None, action)
        
        if isinstance(message, CallbackQuery):
            await message.answer(error_message, show_alert=True)
        else:
            await message.answer(error_message)

    def require_role(self, allowed_roles: List[Roles], permission: str = None):
        """Decorator to check if user has required role"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(message: Message | CallbackQuery, *args, **kwargs):
                user = await self.get_user(message)
                if not user:
                    await message.answer("Please start the bot with /start command")
                    return

                if user.role not in allowed_roles:
                    await self.handle_unauthorized(message, user, permission or "this action")
                    return

                return await func(message, *args, **kwargs)
            return wrapper
        return decorator

    def require_access(self, permission: str):
        """Decorator to check if user has required permission"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(message: Message | CallbackQuery, *args, **kwargs):
                user = await self.get_user(message)
                if not user:
                    await message.answer("Please start the bot with /start command")
                    return

                if not self._check_permission(user, permission):
                    await self.handle_unauthorized(message, user, permission)
                    return

                return await func(message, *args, **kwargs)
            return wrapper
        return decorator

    def _check_permission(self, user: User, permission: str) -> bool:
        """Check if user has the required permission"""
        # Map permissions to roles
        permission_map = {
            "view_dashboard": [Roles.principal, Roles.deputy_principal],
            "view_class": [Roles.homeroom_teacher],
            "view_subjects": [Roles.subject_teacher],
            "view_grades": [Roles.principal, Roles.deputy_principal, Roles.homeroom_teacher, Roles.subject_teacher, Roles.parent],
            "manage_grades": [Roles.principal, Roles.deputy_principal, Roles.homeroom_teacher, Roles.subject_teacher],
            "view_children": [Roles.parent],
            "view_my_grades": [Roles.student]
        }

        allowed_roles = permission_map.get(permission, [])
        return user.role in allowed_roles 