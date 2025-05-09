from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta

from app.db.engine import getSession
from app.db.declaration import Grade, User, Subject
from app.auth_dependency import require_auth

router = APIRouter(
    prefix="/statistics",
    tags=["statistics"],
    dependencies=[Depends(require_auth)]
)

@router.get("/student/{student_id}/overall")
async def get_student_statistics(
    student_id: int,
    session: AsyncSession = Depends(getSession)
):
    """Get overall statistics for a student"""
    # Verify student exists
    result = await session.execute(
        select(User).where(
            User.id == student_id,
            User.role == "student"
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Get average grade per subject
    query = select(
        Subject.name,
        func.avg(Grade.value).label('average'),
        func.count(Grade.id).label('count')
    ).join(
        Grade, Grade.subject_id == Subject.id
    ).where(
        Grade.student_id == student_id
    ).group_by(Subject.name)

    result = await session.execute(query)
    subject_stats = result.all()

    # Calculate overall average
    overall_stats = {
        'subjects': [
            {
                'name': stat.name,
                'average': round(float(stat.average), 2),
                'count': stat.count
            }
            for stat in subject_stats
        ],
        'overall_average': round(
            sum(stat.average * stat.count for stat in subject_stats) /
            sum(stat.count for stat in subject_stats) if subject_stats else 0,
            2
        )
    }

    return overall_stats

@router.get("/student/{student_id}/progress")
async def get_student_progress(
    student_id: int,
    subject_id: int,
    days: int = 30,
    session: AsyncSession = Depends(getSession)
):
    """Get student's progress over time for a specific subject"""
    # Verify student and subject exist
    student_result = await session.execute(
        select(User).where(
            User.id == student_id,
            User.role == "student"
        )
    )
    if not student_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    subject_result = await session.execute(
        select(Subject).where(Subject.id == subject_id)
    )
    if not subject_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )

    # Get grades for the specified time period
    start_date = datetime.utcnow() - timedelta(days=days)
    query = select(Grade).where(
        Grade.student_id == student_id,
        Grade.subject_id == subject_id,
        Grade.created_at >= start_date
    ).order_by(Grade.created_at)

    result = await session.execute(query)
    grades = result.scalars().all()

    # Format the response
    progress_data = [
        {
            'date': grade.created_at.isoformat(),
            'value': grade.value,
            'comment': grade.comment
        }
        for grade in grades
    ]

    return {
        'subject_id': subject_id,
        'student_id': student_id,
        'progress': progress_data
    }

@router.get("/class/{class_id}/subject/{subject_id}")
async def get_class_subject_statistics(
    class_id: int,
    subject_id: int,
    session: AsyncSession = Depends(getSession)
):
    """Get statistics for a specific subject in a class"""
    # Get all grades for the class and subject
    query = select(
        Grade.value,
        func.count(Grade.id).label('count')
    ).join(
        User, Grade.student_id == User.id
    ).where(
        User.class_id == class_id,
        Grade.subject_id == subject_id
    ).group_by(Grade.value)

    result = await session.execute(query)
    grade_distribution = result.all()

    # Calculate statistics
    total_grades = sum(stat.count for stat in grade_distribution)
    if total_grades == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No grades found for this class and subject"
        )

    average = sum(stat.value * stat.count for stat in grade_distribution) / total_grades

    return {
        'class_id': class_id,
        'subject_id': subject_id,
        'total_grades': total_grades,
        'average': round(average, 2),
        'distribution': [
            {
                'grade': stat.value,
                'count': stat.count,
                'percentage': round(stat.count / total_grades * 100, 2)
            }
            for stat in grade_distribution
        ]
    } 