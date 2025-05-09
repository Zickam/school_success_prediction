import logging
import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from app.db.engine import getSession
from app.telegram.setup.auto_init import AutoInitializer
from app.db.declaration import User
from app.db.schemas.user import Roles
from .role_handler import RoleHandler
from ..menu import get_role_menu, get_role_welcome_message

class BotHandler:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.token = os.getenv("BOT_TOKEN")
        if not self.token:
            raise ValueError("BOT_TOKEN environment variable is not set")
        logging.info(f"Bot token: {self.token}")
        self.bot = Bot(token=self.token)
        self.dp = Dispatcher()
        self.role_handler = RoleHandler(session)
        self.auto_init = AutoInitializer(session)
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up command and message handlers"""
        self.dp.message.register(self.start, Command(commands=["start"]))
        self.dp.message.register(self._handle_message)
        self.dp.callback_query.register(self.handle_callback)

    async def _handle_message(self, message: Message):
        """Handle incoming messages"""
        await message.answer(
            "I'm still learning how to handle messages.\n"
            "Please use commands for now."
        )

    async def initialize(self):
        """Initialize the bot and demo data"""
        # Initialize demo data
        await self.auto_init.initialize()

    async def run(self):
        """Run the bot"""
        await self.dp.start_polling(self.bot)

    async def start(self, message: Message):
        """Handle /start command"""
        # Get or create user
        chat_id = message.chat.id
        result = await self.session.execute(
            select(User).where(User.chat_id == chat_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create new user with student role by default
            user = User(
                chat_id=chat_id,
                name=message.from_user.full_name,
                role=Roles.student
            )
            self.session.add(user)
            await self.session.commit()

        # Send welcome message with role-specific menu
        welcome_message = get_role_welcome_message(user.role, user.name)
        menu = get_role_menu(user.role)
        
        await message.answer(
            text=welcome_message,
            reply_markup=menu
        )

    async def dashboard(self, message: Message):
        """Show school dashboard (admin only)"""
        user = await self.role_handler.get_user(message)
        if not user or user.role not in [Roles.principal, Roles.deputy_principal]:
            await message.answer("You don't have permission to view the dashboard")
            return
        # Implementation for dashboard view
        pass

    async def my_class(self, message: Message):
        """Show homeroom teacher's class"""
        user = await self.role_handler.get_user(message)
        if not user or user.role != Roles.homeroom_teacher:
            await message.answer("You don't have permission to view this class")
            return
        # Implementation for class view
        pass

    async def my_subjects(self, message: Message):
        """Show subject teacher's subjects"""
        user = await self.role_handler.get_user(message)
        if not user or user.role != Roles.subject_teacher:
            await message.answer("You don't have permission to view these subjects")
            return
        # Implementation for subjects view
        pass

    async def view_grades(self, message: Message, target_uuid: str):
        """View grades with access control"""
        user = await self.role_handler.get_user(message)
        if not user:
            await message.answer("Please start the bot with /start command")
            return

        if not await self.role_handler.check_role_access(user, "view_grades", target_uuid):
            await message.answer("You don't have permission to view these grades")
            return
        # Implementation for grades view
        pass

    async def manage_grades(self, message: Message, target_uuid: str):
        """Manage grades with access control"""
        user = await self.role_handler.get_user(message)
        if not user:
            await message.answer("Please start the bot with /start command")
            return

        if not await self.role_handler.check_role_access(user, "manage_grades", target_uuid):
            await message.answer("You don't have permission to manage these grades")
            return
        # Implementation for grades management
        pass

    async def my_children(self, message: Message):
        """Show parent's children"""
        user = await self.role_handler.get_user(message)
        if not user or user.role != Roles.parent:
            await message.answer("You don't have permission to view children")
            return
        # Implementation for children view
        pass

    async def my_grades(self, message: Message):
        """Show student's own grades"""
        user = await self.role_handler.get_user(message)
        if not user or user.role != Roles.student:
            await message.answer("You don't have permission to view these grades")
            return
        # Implementation for student's grades view
        pass

    async def settings(self, message: Message):
        """Show settings menu"""
        chat_id = message.chat.id
        result = await self.session.execute(
            select(User).where(User.chat_id == chat_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return

        # Create settings menu based on role
        settings_menu = get_role_menu(user.role)
        
        if isinstance(message, CallbackQuery):
            await message.message.edit_text(
                text="Settings",
                reply_markup=settings_menu
            )
        else:
            await message.answer(
                text="Settings",
                reply_markup=settings_menu
            )

    async def handle_callback(self, callback: CallbackQuery):
        """Handle callback queries"""
        await callback.answer()

        # Map callback data to handler methods
        handlers = {
            "dashboard": self.dashboard,
            "my_class": self.my_class,
            "my_subjects": self.my_subjects,
            "my_children": self.my_children,
            "my_grades": self.my_grades,
            "settings": self.settings
        }

        handler = handlers.get(callback.data)
        if handler:
            await handler(callback) 