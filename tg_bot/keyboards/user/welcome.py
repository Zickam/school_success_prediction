from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.schemas.user import Roles

def keyboardChooseRole():
    keyboard = InlineKeyboardBuilder()

    for role in Roles:
        keyboard.add(InlineKeyboardButton(text=role, callback_data=f"role|{role}"))

    return keyboard.as_markup()