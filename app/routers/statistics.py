from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.session import get_session
from app.db.models import Grade, Attendance, AttendanceStatus, User
from app.core.auth import get_current_user

router = APIRouter(prefix="/statistics", tags=["statistics"])

@router.get("/student/{student_id}")
async def get_student_statistics(
    student_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a specific student"""
    try:
        # Get all grades for the student
        grades = await db.query(Grade).filter(Grade.student_id == student_id).all()
        
        # Count grades
        grade_counts = {}
        for grade in grades:
            value = grade.value
            grade_counts[value] = grade_counts.get(value, 0) + 1
        
        # Get attendance data
        attendance_records = await db.query(Attendance).filter(Attendance.student_id == student_id).all()
        
        attendance_stats = {
            AttendanceStatus.PRESENT.value: 0,
            AttendanceStatus.ABSENT.value: 0,
            AttendanceStatus.LATE.value: 0
        }
        
        for record in attendance_records:
            status = record.status
            attendance_stats[status] = attendance_stats.get(status, 0) + 1
        
        # Calculate average grade
        average_grade = None
        if grade_counts:
            total = sum(grade * count for grade, count in grade_counts.items())
            count = sum(grade_counts.values())
            average_grade = total / count
        
        # Calculate attendance rate
        attendance_rate = None
        total_days = sum(attendance_stats.values())
        if total_days > 0:
            attendance_rate = (attendance_stats[AttendanceStatus.PRESENT.value] / total_days) * 100
        
        return {
            "grade_distribution": grade_counts,
            "average_grade": average_grade,
            "attendance_stats": {
                "present": attendance_stats[AttendanceStatus.PRESENT.value],
                "absent": attendance_stats[AttendanceStatus.ABSENT.value],
                "late": attendance_stats[AttendanceStatus.LATE.value]
            },
            "attendance_rate": attendance_rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 