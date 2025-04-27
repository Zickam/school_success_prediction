import logging
from uuid import UUID

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from tg_bot.filters import IsPrivate, IsPrivateCallback
from tg_bot import keyboards
from tg_bot.config import httpx_client
from tg_bot.common import updateUserDecorator
from app.db.schemas.user import Roles

router = Router()
router.message.filter(IsPrivate())
router.callback_query.filter(IsPrivateCallback())

async def get_user_classes(user_uuid: str) -> list:
    """Get all classes for a user"""
    resp = await httpx_client.get(f"schools/users/{user_uuid}/classes")
    if resp.status_code == 200:
        return resp.json()
    return []

async def get_class_details(class_uuid: str) -> dict:
    """Get detailed information about a class"""
    resp = await httpx_client.get(f"schools/classes/{class_uuid}")
    if resp.status_code == 200:
        return resp.json()
    return {}

async def get_class_teachers(class_uuid: str) -> list:
    """Get all teachers in a class"""
    resp = await httpx_client.get(f"schools/classes/{class_uuid}/teachers")
    if resp.status_code == 200:
        return resp.json()
    return []

async def get_class_students(class_uuid: str) -> list:
    """Get all students in a class"""
    resp = await httpx_client.get(f"schools/classes/{class_uuid}/students")
    if resp.status_code == 200:
        return resp.json()
    return []

@router.message(Command("start"))
@updateUserDecorator
async def start(msg: Message, state: FSMContext):
    # Get user data
    data = await state.get_data()
    if "user_uuid" not in data:
        await msg.answer("Ошибка: пользователь не найден. Попробуйте перезапустить бота.")
        return

    # Get command arguments
    args = msg.text.split()
    if len(args) > 1:  # Has class UUID
        try:
            class_uuid = UUID(args[1])
            # Get class info
            class_resp = await httpx_client.get(f"schools/classes/{str(class_uuid)}")
            if class_resp.status_code == 200:
                class_info = class_resp.json()
                await msg.answer(
                    f"Привет! Это бот для оценки успехов школьников. "
                    f"Тебя пригласили в класс: {class_info['class_name']}",
                    reply_markup=keyboards.user.welcome.keyboardAcceptInvite(str(class_uuid))
                )
            else:
                await msg.answer(
                    "Привет! Это бот для оценки успехов школьников. "
                    "Скорее всего с твоей ссылкой для приглашения в класс что-то не так, "
                    "обратись к учителю за получением новой"
                )
            return
        except ValueError:
            await msg.answer(
                "Привет! Это бот для оценки успехов школьников. "
                "Скорее всего с твоей ссылкой для приглашения в класс что-то не так, "
                "обратись к учителю за получением новой"
            )
            return

    # Get user's classes
    classes = await get_user_classes(data["user_uuid"])
    
    if not classes:
        await msg.answer(
            "Привет! Это бот для оценки успехов школьников. "
            "Обратись к своему учителю для получения приглашения в класс!"
        )
        return

    # Build message with user's classes and details
    message = ["Привет! Это бот для оценки успехов школьников.\n"]
    
    for class_info in classes:
        message.append(f"\n📚 Класс: {class_info['class_name']}")
        
        # Get class details
        class_details = await get_class_details(class_info['uuid'])
        if class_details:
            message.append(f"🏫 Школа: {class_details.get('school', {}).get('facility_name', 'Не указана')}")
        
        # Get teachers
        teachers = await get_class_teachers(class_info['uuid'])
        if teachers:
            message.append("👨‍🏫 Учителя:")
            for teacher in teachers:
                message.append(f"  • {teacher['name']}")
        
        # Get students count
        students = await get_class_students(class_info['uuid'])
        if students:
            message.append(f"👥 Учеников в классе: {len(students)}")
        
        # Add class invite link for teachers
        if msg.from_user.id in [t['chat_id'] for t in teachers]:
            invite_link = await httpx_client.get(f"schools/classes/{class_info['uuid']}/invite_link")
            if invite_link.status_code == 200:
                message.append(f"\n🔗 Ссылка для приглашения: {invite_link.text}")

    await msg.answer("\n".join(message))

@router.callback_query(F.data.startswith("join|"))
@updateUserDecorator
async def joinClass(call: CallbackQuery, state: FSMContext):
    try:
        class_uuid = call.data.replace("join|", "")
        data = await state.get_data()
        
        if "user_uuid" not in data:
            await call.message.answer("Ошибка: пользователь не найден. Попробуйте перезапустить бота командой /start")
            return

        resp = await httpx_client.post(
            f"schools/classes/{class_uuid}/join",
            params={
                "user_uuid": data["user_uuid"]
            }
        )

        if resp.status_code == 409:
            await call.message.answer("Ты уже состоишь в этом классе")
        elif resp.status_code == 200:
            class_info = resp.json()
            await call.message.answer(f"Ты присоединился к классу {class_info['class_name']}")
        else:
            await call.message.answer(f"Произошла ошибка: {resp.status_code}, {resp.text}")
    except Exception as e:
        logging.error(f"Error joining class: {str(e)}")
        await call.message.answer("Произошла ошибка при присоединении к классу. Попробуйте позже.")