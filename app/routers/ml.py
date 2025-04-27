from __future__ import annotations
from typing import List, Dict
from uuid import UUID
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..db.engine import getSession
from ..db.declaration import User, Class, Grade, Subject
from ..db.schemas.user import User as UserSchema, Roles
from pydantic import BaseModel

router = APIRouter(
    prefix="/ml",
    tags=["machine_learning"]
)

class StudentStats(BaseModel):
    student_uuid: UUID
    student_name: str
    average_grade: float
    attendance_rate: float
    subject_performance: Dict[str, float]
    predicted_success_rate: float
    risk_factors: List[str]
    recommendations: List[str]

class ClassPrediction(BaseModel):
    class_uuid: UUID
    class_name: str
    average_success_rate: float
    at_risk_students: List[StudentStats]
    top_performers: List[StudentStats]
    subject_analysis: Dict[str, float]
    class_recommendations: List[str]

@router.get("/students/{student_uuid}/predictions", response_model=StudentStats)
async def get_student_predictions(
    student_uuid: UUID,
    session: AsyncSession = Depends(getSession)
):
    # Get student
    result = await session.execute(
        select(User).where(User.uuid == student_uuid)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.role != Roles.STUDENT:
        raise HTTPException(status_code=400, detail="User is not a student")

    # Get student's grades
    result = await session.execute(
        select(Grade).where(Grade.user_uuid == student_uuid)
    )
    grades = result.scalars().all()

    # Mock predictions
    subject_performance = {}
    for grade in grades:
        subject = await session.get(Subject, grade.subject_uuid)
        subject_performance[subject.name] = grade.value

    # Mock data
    return StudentStats(
        student_uuid=student.uuid,
        student_name=student.name,
        average_grade=sum(g.value for g in grades) / len(grades) if grades else 0,
        attendance_rate=random.uniform(0.7, 1.0),
        subject_performance=subject_performance,
        predicted_success_rate=random.uniform(0.5, 1.0),
        risk_factors=["Low attendance in Mathematics", "Declining grades in Physics"],
        recommendations=["Consider additional tutoring in Mathematics", "Review study schedule"]
    )

@router.get("/classes/{class_id}/predictions", response_model=ClassPrediction)
async def get_class_predictions(
    class_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    # Get class
    result = await session.execute(
        select(Class).options(selectinload(Class.users)).where(Class.uuid == class_id)
    )
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")

    # Get students in class
    students = [user for user in class_.users if user.role == Roles.STUDENT]
    
    # Get predictions for each student
    student_predictions = []
    for student in students:
        prediction = await get_student_predictions(student.uuid, session)
        student_predictions.append(prediction)

    # Mock data
    return ClassPrediction(
        class_uuid=class_.uuid,
        class_name=class_.class_name,
        average_success_rate=sum(p.predicted_success_rate for p in student_predictions) / len(student_predictions),
        at_risk_students=[p for p in student_predictions if p.predicted_success_rate < 0.6],
        top_performers=[p for p in student_predictions if p.predicted_success_rate > 0.8],
        subject_analysis={
            "Mathematics": random.uniform(0.6, 0.9),
            "Physics": random.uniform(0.6, 0.9),
            "Chemistry": random.uniform(0.6, 0.9)
        },
        class_recommendations=[
            "Consider group study sessions for Mathematics",
            "Schedule regular progress reviews",
            "Implement peer tutoring program"
        ]
    )

@router.get("/teachers/{teacher_uuid}/dashboard", response_model=Dict[str, List[ClassPrediction]])
async def get_teacher_dashboard(
    teacher_uuid: UUID,
    session: AsyncSession = Depends(getSession)
):
    # Get teacher
    result = await session.execute(
        select(User).options(selectinload(User.classes)).where(User.uuid == teacher_uuid)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    if teacher.role != Roles.TEACHER:
        raise HTTPException(status_code=400, detail="User is not a teacher")

    # Get predictions for each class
    class_predictions = []
    for class_ in teacher.classes:
        prediction = await get_class_predictions(class_.uuid, session)
        class_predictions.append(prediction)

    # Mock data
    return {
        "class_predictions": class_predictions,
        "overall_statistics": {
            "total_students": sum(len(p.at_risk_students) + len(p.top_performers) for p in class_predictions),
            "at_risk_students": sum(len(p.at_risk_students) for p in class_predictions),
            "top_performers": sum(len(p.top_performers) for p in class_predictions),
            "average_success_rate": sum(p.average_success_rate for p in class_predictions) / len(class_predictions)
        }
    } 