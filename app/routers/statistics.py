from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID

from app.db.session import get_session
from app.db.models import Grade, Attendance, AttendanceStatus, User, Student
from app.core.auth import get_current_user
from app.db.schemas.user import Roles

router = APIRouter(prefix="/statistics", tags=["statistics"])

@router.get("/student/{student_id}")
async def get_student_statistics(
    student_id: UUID,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a specific student"""
    try:
        # Check if student exists
        student = db.query(Student).filter(Student.uuid == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with UUID {student_id} not found"
            )
        
        # Check permissions
        if current_user.role == Roles.student and str(current_user.uuid) != str(student_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own statistics"
            )
        
        # Get all grades for the student
        grades = db.query(Grade).filter(Grade.student_uuid == student_id).all()
        
        # Count grades
        grade_counts = {}
        for grade in grades:
            value = str(grade.value)  # Convert to string for JSON serialization
            grade_counts[value] = grade_counts.get(value, 0) + 1
        
        # Get attendance data
        attendance_records = db.query(Attendance).filter(Attendance.student_uuid == student_id).all()
        
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
            total = sum(int(grade) * count for grade, count in grade_counts.items())
            count = sum(grade_counts.values())
            average_grade = round(total / count, 2)
        
        # Calculate attendance rate
        attendance_rate = None
        total_days = sum(attendance_stats.values())
        if total_days > 0:
            attendance_rate = round((attendance_stats[AttendanceStatus.PRESENT.value] / total_days) * 100, 1)
        
        # Format response to match bot's expectations
        return {
            "grades": {
                "distribution": grade_counts,
                "average": average_grade
            },
            "attendance": {
                "total_days": total_days,
                "present_days": attendance_stats[AttendanceStatus.PRESENT.value],
                "absent_days": attendance_stats[AttendanceStatus.ABSENT.value],
                "late_days": attendance_stats[AttendanceStatus.LATE.value]
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 