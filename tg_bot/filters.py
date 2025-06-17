from aiogram.enums import ChatType
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


class IsPrivate(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == ChatType.PRIVATE


class IsPrivateCallback(Filter):
    async def __call__(self, call: CallbackQuery) -> bool:
        return call.message.chat.type == ChatType.PRIVATE
