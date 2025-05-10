from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from tg_bot.filters import IsPrivate
from tg_bot.api_client import make_api_request

router = Router()
router.message.filter(IsPrivate())

@router.message(Command("grades"))
async def show_grades_statistics(message: Message):
    """Show grade statistics"""
    # Get all grades for statistics
    response = await make_api_request(
        "GET",
        f"/grades",
        params={"student_id": message.from_user.id}
    )
    
    if response:
        # Count grades
        grade_counts = {}
        for grade in response:
            value = grade['value']
            grade_counts[value] = grade_counts.get(value, 0) + 1
        
        # Get attendance data
        attendance_response = await make_api_request(
            "GET",
            f"/attendance",
            params={"student_id": message.from_user.id}
        )
        
        attendance_stats = {
            "present": 0,
            "absent": 0,
            "late": 0
        }
        
        if attendance_response:
            for record in attendance_response:
                status = record['status']
                attendance_stats[status] = attendance_stats.get(status, 0) + 1
        
        # Format statistics message
        text = "📊 Your Statistics:\n\n"
        
        # Grade distribution
        for grade in sorted(grade_counts.keys(), reverse=True):
            text += f"Grade {grade}: {grade_counts[grade]} times\n"
        
        # Calculate average
        if grade_counts:
            total = sum(grade * count for grade, count in grade_counts.items())
            count = sum(grade_counts.values())
            average = total / count
            text += f"\nAverage Grade: {average:.2f}\n"
        
        # Attendance statistics
        text += f"\nAbsent Days: {attendance_stats['absent']}\n"
        text += f"Late Days: {attendance_stats['late']}\n"
        
        # Calculate attendance rate
        total_days = sum(attendance_stats.values())
        if total_days > 0:
            attendance_rate = (attendance_stats['present'] / total_days) * 100
            text += f"Attendance Rate: {attendance_rate:.1f}%"
        
        await message.answer(text)
    else:
        await message.answer("❌ Failed to fetch grades") 