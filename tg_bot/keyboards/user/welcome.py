from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.schemas.user import Roles

def keyboardChooseRole():
    keyboard = InlineKeyboardBuilder()

    for role in Roles:
        keyboard.add(InlineKeyboardButton(text=role, callback_data=f"role|{role}"))

    return keyboard.as_markup()

def keyboardAcceptInvite(class_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text="Принять", callback_data=f"join|{class_id}"))
    keyboard.add(InlineKeyboardButton(text="Отклонить", callback_data="menu"))

    return keyboard.as_markup()