from aiogram.enums import ChatType
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

# from app.models import user as user_models
#
#
# class IsAdmin(Filter):
#     def __init__(self) -> None: ...
#
#     async def __call__(self, message: Message) -> bool:
#         is_admin = await user_models.User.filter(role="admin", user_id=message.chat.id)
#         if is_admin:
#             return True
#
#         return False
#
#
# class IsAdminCallback(Filter):
#     def __init__(self) -> None: ...
#
#     async def __call__(self, call: CallbackQuery) -> bool:
#         is_admin = await user_models.User.filter(
#             role="admin", user_id=call.message.chat.id
#         )
#         if is_admin:
#             return True
#
#         return False


class IsPrivate(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == ChatType.PRIVATE


class IsPrivateCallback(Filter):
    async def __call__(self, call: CallbackQuery) -> bool:
        return call.message.chat.type == ChatType.PRIVATE
