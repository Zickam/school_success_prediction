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
    if len(args) > 1:  # Has invitation code
        try:
            # Parse invitation code (format: invite|invitation_uuid)
            parts = args[1].split('|')
            if len(parts) != 2 or parts[0] != "invite":
                raise ValueError("Invalid invitation format")
            
            invitation_uuid = UUID(parts[1])
            
            # Get invitation details
            invite_resp = await httpx_client.get(f"invitations/{str(invitation_uuid)}")
            if invite_resp.status_code == 200:
                invitation = invite_resp.json()
                
                # Customize message based on invitation type
                if invitation["type"] == "class_student":
                    message = (
                        f"Привет! Тебя пригласили в класс: {invitation['class_name']}\n"
                        "После присоединения ты сможешь видеть свои оценки и прогнозы успеваемости."
                    )
                elif invitation["type"] == "class_teacher":
                    message = (
                        f"Привет! Вас пригласили в качестве учителя в класс: {invitation['class_name']}\n"
                        "После присоединения вы сможете управлять классом и отслеживать успеваемость учеников."
                    )
                elif invitation["type"] == "subject_teacher":
                    message = (
                        f"Привет! Вас пригласили преподавать предмет: {invitation['subject_name']}\n"
                        "После присоединения вы сможете управлять успеваемостью по своему предмету."
                    )
                elif invitation["type"] == "parent_child":
                    message = (
                        f"Привет! Вас пригласили подключиться к профилю ученика: {invitation['child_name']}\n"
                        "После присоединения вы сможете следить за успеваемостью вашего ребенка."
                    )
                else:
                    message = (
                        f"Привет! Вас пригласили в систему.\n"
                        "После присоединения вы получите доступ к соответствующим функциям."
                    )
                
                # Add expiration info
                message += f"\n\nСсылка действительна до: {invitation['expires_at']}"
                
                await msg.answer(
                    message,
                    reply_markup=keyboards.user.welcome.keyboardAcceptInvite(str(invitation_uuid))
                )
            else:
                await msg.answer(
                    "Привет! Это бот для оценки успехов школьников.\n"
                    "Ссылка для приглашения недействительна. Пожалуйста, обратитесь к администратору за новой ссылкой."
                )
            return
        except ValueError:
            await msg.answer(
                "Привет! Это бот для оценки успехов школьников.\n"
                "Ссылка для приглашения недействительна. Пожалуйста, обратитесь к администратору за новой ссылкой."
            )
            return

    # Get user's classes
    classes = await get_user_classes(data["user_uuid"])
    
    if not classes:
        await msg.answer(
            "Привет! Это бот для оценки успехов школьников.\n"
            "Для начала работы вам нужно получить приглашение от администратора школы."
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
                role_emoji = "👨‍🏫" if teacher['role'] == Roles.homeroom_teacher else "📚"
                message.append(f"  • {role_emoji} {teacher['name']}")
        
        # Get students count
        students = await get_class_students(class_info['uuid'])
        if students:
            message.append(f"👥 Учеников в классе: {len(students)}")
        
        # Add invitation options based on user role
        user_role = await get_user_role(data["user_uuid"])
        if user_role in [Roles.principal, Roles.deputy_principal, Roles.homeroom_teacher]:
            message.append("\n📨 Создать приглашения:")
            message.append("  • /invite_student - Пригласить ученика")
            message.append("  • /invite_teacher - Пригласить учителя")
            if user_role in [Roles.principal, Roles.deputy_principal]:
                message.append("  • /invite_parent - Пригласить родителя")

    await msg.answer("\n".join(message))

@router.callback_query(F.data.startswith("join|"))
@updateUserDecorator
async def joinClass(call: CallbackQuery, state: FSMContext):
    try:
        invitation_uuid = call.data.replace("join|", "")
        data = await state.get_data()
        
        if "user_uuid" not in data:
            await call.message.answer("Ошибка: пользователь не найден. Попробуйте перезапустить бота командой /start")
            return

        resp = await httpx_client.post(
            f"invitations/{invitation_uuid}/accept",
            params={
                "user_uuid": data["user_uuid"]
            }
        )

        if resp.status_code == 409:
            await call.message.answer("Вы уже приняли это приглашение")
        elif resp.status_code == 200:
            invitation = resp.json()
            
            # Customize success message based on invitation type
            if invitation["type"] == "class_student":
                message = f"Вы успешно присоединились к классу {invitation['class_name']}!"
            elif invitation["type"] == "class_teacher":
                message = f"Вы успешно присоединились к классу {invitation['class_name']} в качестве учителя!"
            elif invitation["type"] == "subject_teacher":
                message = f"Вы успешно присоединились к предмету {invitation['subject_name']}!"
            elif invitation["type"] == "parent_child":
                message = f"Вы успешно подключились к профилю ученика {invitation['child_name']}!"
            else:
                message = "Вы успешно присоединились к системе!"
            
            message += "\nТеперь вы можете использовать все доступные функции бота."
            await call.message.answer(message)
        else:
            await call.message.answer(f"Произошла ошибка: {resp.status_code}, {resp.text}")
    except Exception as e:
        logging.error(f"Error accepting invitation: {str(e)}")
        await call.message.answer("Произошла ошибка при принятии приглашения. Попробуйте позже.")