from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from app.db.engine import getSession
from app.db.models import Grade, Attendance, AttendanceStatus, User, Subject
from app.core.auth import get_current_user
from app.db.schemas.user import Roles
from app.db.schemas.statistics import UserStatistics, ClassStatistics, SchoolStatistics

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/users/{user_uuid}", response_model=UserStatistics)
async def get_user_statistics(
    user_uuid: str, db: AsyncSession = Depends(getSession)
) -> UserStatistics:

    stmt = select(User).where(User.uuid == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with UUID {user_uuid} not found",
        )

    stmt = select(Grade).where(Grade.user_uuid == user_uuid)
    result = await db.execute(stmt)
    grades = result.scalars().all()

    stmt = select(Attendance).where(Attendance.user_uuid == user_uuid)
    result = await db.execute(stmt)
    attendance_records = result.scalars().all()

    total_grades = len(grades)
    average_grade = (
        sum(grade.value for grade in grades) / total_grades if total_grades > 0 else 0
    )

    total_attendance = len(attendance_records)
    present_count = sum(
        1 for record in attendance_records if record.status == AttendanceStatus.PRESENT
    )
    attendance_rate = (
        (present_count / total_attendance) * 100 if total_attendance > 0 else 0
    )

    subject_performance = {}
    for grade in grades:
        subject = await db.get(Subject, grade.subject_uuid)
        if subject:
            if subject.name not in subject_performance:
                subject_performance[subject.name] = []
            subject_performance[subject.name].append(grade.value)

    for subject in subject_performance:
        subject_performance[subject] = sum(subject_performance[subject]) / len(
            subject_performance[subject]
        )

    risk_factors = []
    if attendance_rate < 80:
        risk_factors.append("Low attendance rate")
    if average_grade < 3.5:
        risk_factors.append("Below average grades")
    for subject, avg in subject_performance.items():
        if avg < 3.0:
            risk_factors.append(f"Struggling in {subject}")

    recommendations = []
    if "Low attendance rate" in risk_factors:
        recommendations.append("Consider improving attendance")
    if "Below average grades" in risk_factors:
        recommendations.append("Consider seeking additional help or tutoring")
    for subject in subject_performance:
        if subject_performance[subject] < 3.0:
            recommendations.append(f"Consider extra practice in {subject}")

    return UserStatistics(
        user_uuid=user.uuid,
        user_name=user.name,
        average_grade=average_grade,
        attendance_rate=attendance_rate,
        subject_performance=subject_performance,
        risk_factors=risk_factors,
        recommendations=recommendations,
    )


@router.get("/student/{student_id}")
async def get_student_statistics(
    student_id: UUID,
    db: AsyncSession = Depends(getSession),
):

    try:
        stmt = select(User).where(
            and_(User.uuid == student_id, User.role == Roles.student)
        )
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with UUID {student_id} not found",
            )

        stmt = select(Grade).where(Grade.user_uuid == student_id)
        result = await db.execute(stmt)
        grades = result.scalars().all()

        grade_counts = {}
        for grade in grades:
            value = str(grade.value)
            grade_counts[value] = grade_counts.get(value, 0) + 1

        stmt = select(Attendance).where(Attendance.user_uuid == student_id)
        result = await db.execute(stmt)
        attendance_records = result.scalars().all()

        attendance_stats = {
            AttendanceStatus.PRESENT.value: 0,
            AttendanceStatus.ABSENT.value: 0,
            AttendanceStatus.LATE.value: 0,
        }

        for record in attendance_records:
            _status = record.status
            attendance_stats[_status] = attendance_stats.get(_status, 0) + 1

        average_grade = None
        if grade_counts:
            total = sum(int(grade) * count for grade, count in grade_counts.items())
            count = sum(grade_counts.values())
            average_grade = round(total / count, 2)

        attendance_rate = None
        total_days = sum(attendance_stats.values())
        if total_days > 0:
            attendance_rate = round(
                (attendance_stats[AttendanceStatus.PRESENT.value] / total_days) * 100, 1
            )

        return {
            "grades": {"distribution": grade_counts, "average": average_grade},
            "attendance": {
                "total_days": total_days,
                "present_days": attendance_stats[AttendanceStatus.PRESENT.value],
                "absent_days": attendance_stats[AttendanceStatus.ABSENT.value],
                "late_days": attendance_stats[AttendanceStatus.LATE.value],
            },
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format: {str(e)}",
        )
    except HTTPException as ex:
        raise ex
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/class/{class_id}/attendance")
async def get_class_attendance(
    class_id: str,
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(getSession),
) -> Dict[str, Any]:

    students_query = select(User).where(
        and_(User.role == Roles.student, User.classes.any(uuid=class_id))
    )
    result = await db.execute(students_query)
    students = result.scalars().all()

    if not students:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No students found in this class",
        )

    attendance_query = select(Attendance).where(
        and_(
            Attendance.user_uuid.in_([s.uuid for s in students]),
            Attendance.date >= start_date,
            Attendance.date <= end_date,
        )
    )
    result = await db.execute(attendance_query)
    attendance_records = result.scalars().all()

    total_days = (end_date - start_date).days + 1
    total_possible_attendance = len(students) * total_days
    present_count = sum(
        1 for record in attendance_records if record.status == AttendanceStatus.PRESENT
    )
    absent_count = sum(
        1 for record in attendance_records if record.status == AttendanceStatus.ABSENT
    )
    late_count = sum(
        1 for record in attendance_records if record.status == AttendanceStatus.LATE
    )

    return {
        "total_days": total_days,
        "total_students": len(students),
        "total_possible_attendance": total_possible_attendance,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "attendance_rate": (
            (present_count / total_possible_attendance) * 100
            if total_possible_attendance > 0
            else 0
        ),
    }


@router.get("/class/{class_id}/grades")
async def get_class_grades(
    class_id: str, subject_id: str = None, db: AsyncSession = Depends(getSession)
) -> Dict[str, Any]:

    students_query = select(User).where(
        and_(User.role == Roles.student, User.classes.any(uuid=class_id))
    )
    result = await db.execute(students_query)
    students = result.scalars().all()

    if not students:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No students found in this class",
        )

    grade_query = select(Grade).where(Grade.user_uuid.in_([s.uuid for s in students]))
    if subject_id:
        grade_query = grade_query.where(Grade.subject_uuid == subject_id)

    result = await db.execute(grade_query)
    grades = result.scalars().all()

    if not grades:
        return {
            "total_students": len(students),
            "total_grades": 0,
            "average_grade": 0,
            "min_grade": 0,
            "max_grade": 0,
            "grade_distribution": {},
        }

    grade_values = [grade.value for grade in grades]
    grade_distribution = {}
    for grade in grade_values:
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

    return {
        "total_students": len(students),
        "total_grades": len(grades),
        "average_grade": sum(grade_values) / len(grade_values),
        "min_grade": min(grade_values),
        "max_grade": max(grade_values),
        "grade_distribution": grade_distribution,
    }


@router.get("/student/{student_id}/attendance")
async def get_student_attendance(
    student_id: str,
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(getSession),
) -> Dict[str, Any]:

    student_query = select(User).where(
        and_(User.uuid == student_id, User.role == Roles.student)
    )
    result = await db.execute(student_query)
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    attendance_query = select(Attendance).where(
        and_(
            Attendance.user_uuid == student_id,
            Attendance.date >= start_date,
            Attendance.date <= end_date,
        )
    )
    result = await db.execute(attendance_query)
    attendance_records = result.scalars().all()

    total_days = (end_date - start_date).days + 1
    present_count = sum(
        1 for record in attendance_records if record.status == AttendanceStatus.PRESENT
    )
    absent_count = sum(
        1 for record in attendance_records if record.status == AttendanceStatus.ABSENT
    )
    late_count = sum(
        1 for record in attendance_records if record.status == AttendanceStatus.LATE
    )

    return {
        "total_days": total_days,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "attendance_rate": (present_count / total_days) * 100 if total_days > 0 else 0,
    }


@router.get("/student/{student_id}/grades")
async def get_student_grades(
    student_id: str, subject_id: str = None, db: AsyncSession = Depends(getSession)
) -> Dict[str, Any]:

    student_query = select(User).where(
        and_(User.uuid == student_id, User.role == Roles.student)
    )
    result = await db.execute(student_query)
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    grade_query = select(Grade).where(Grade.user_uuid == student_id)
    if subject_id:
        grade_query = grade_query.where(Grade.subject_uuid == subject_id)

    result = await db.execute(grade_query)
    grades = result.scalars().all()

    if not grades:
        return {
            "total_grades": 0,
            "average_grade": 0,
            "min_grade": 0,
            "max_grade": 0,
            "grade_distribution": {},
        }

    grade_values = [grade.value for grade in grades]
    grade_distribution = {}
    for grade in grade_values:
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

    return {
        "total_grades": len(grades),
        "average_grade": sum(grade_values) / len(grade_values),
        "min_grade": min(grade_values),
        "max_grade": max(grade_values),
        "grade_distribution": grade_distribution,
    }


@router.get("/user/{user_id}/attendance")
async def get_user_attendance(
    user_id: str,
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(getSession),
) -> Dict[str, Any]:

    user_query = select(User).where(
        and_(User.uuid == user_id, User.role == Roles.student)
    )
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    attendance_query = select(Attendance).where(
        and_(
            Attendance.user_uuid == user_id,
            Attendance.date >= start_date,
            Attendance.date <= end_date,
        )
    )
    result = await db.execute(attendance_query)
    attendance_records = result.scalars().all()

    total_days = (end_date - start_date).days + 1
    present_count = sum(
        1 for record in attendance_records if record.status == AttendanceStatus.PRESENT
    )
    absent_count = sum(
        1 for record in attendance_records if record.status == AttendanceStatus.ABSENT
    )
    late_count = sum(
        1 for record in attendance_records if record.status == AttendanceStatus.LATE
    )

    return {
        "total_days": total_days,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "attendance_rate": (present_count / total_days) * 100 if total_days > 0 else 0,
    }


@router.get("/user/{user_id}/grades")
async def get_user_grades(
    user_id: str, subject_id: str = None, db: AsyncSession = Depends(getSession)
) -> Dict[str, Any]:

    user_query = select(User).where(
        and_(User.uuid == user_id, User.role == Roles.student)
    )
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    grade_query = select(Grade).where(Grade.user_uuid == user_id)
    if subject_id:
        grade_query = grade_query.where(Grade.subject_uuid == subject_id)

    result = await db.execute(grade_query)
    grades = result.scalars().all()

    if not grades:
        return {
            "total_grades": 0,
            "average_grade": 0,
            "min_grade": 0,
            "max_grade": 0,
            "grade_distribution": {},
        }

    grade_values = [grade.value for grade in grades]
    grade_distribution = {}
    for grade in grade_values:
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

    return {
        "total_grades": len(grades),
        "average_grade": sum(grade_values) / len(grade_values),
        "min_grade": min(grade_values),
        "max_grade": max(grade_values),
        "grade_distribution": grade_distribution,
    }
