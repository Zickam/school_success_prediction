from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.engine import getSession
from app.db.models import Grade, User, Subject
from app.db.schemas.grade import GradeCreate, GradeUpdate, GradeResponse
from app.db.schemas.user import Roles
from app.auth_dependency import require_auth

router = APIRouter(
    prefix="/grades",
    tags=["grades"],
)


@router.get("/", response_model=List[GradeResponse])
async def get_grades(
    skip: int = 0, limit: int = 100, session: AsyncSession = Depends(getSession)
):

    result = await session.execute(select(Grade).offset(skip).limit(limit))
    grades = result.scalars().all()
    return grades


@router.post("/", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
async def create_grade(
    grade_data: GradeCreate, session: AsyncSession = Depends(getSession)
):

    result = await session.execute(
        select(User).where(
            User.uuid == grade_data.user_uuid, User.role == Roles.student
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student not found or not a student",
        )

    result = await session.execute(
        select(Subject).where(Subject.uuid == grade_data.subject_uuid)
    )
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Subject not found"
        )

    grade = Grade(**grade_data.model_dump())
    session.add(grade)
    await session.commit()
    await session.refresh(grade)
    return grade


@router.get("/{grade_id}", response_model=GradeResponse)
async def get_grade(grade_id: UUID, session: AsyncSession = Depends(getSession)):

    result = await session.execute(select(Grade).where(Grade.uuid == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found"
        )
    return grade


@router.put("/{grade_id}", response_model=GradeResponse)
async def update_grade(
    grade_id: UUID, grade_data: GradeUpdate, session: AsyncSession = Depends(getSession)
):

    result = await session.execute(select(Grade).where(Grade.uuid == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found"
        )

    if grade_data.user_uuid:
        result = await session.execute(
            select(User).where(
                User.uuid == grade_data.user_uuid, User.role == Roles.student
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student not found or not a student",
            )

    if grade_data.subject_uuid:
        result = await session.execute(
            select(Subject).where(Subject.uuid == grade_data.subject_uuid)
        )
        subject = result.scalar_one_or_none()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Subject not found"
            )

    for key, value in grade_data.model_dump(exclude_unset=True).items():
        setattr(grade, key, value)

    await session.commit()
    await session.refresh(grade)
    return grade


@router.delete("/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grade(grade_id: UUID, session: AsyncSession = Depends(getSession)):

    result = await session.execute(select(Grade).where(Grade.uuid == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found"
        )

    await session.delete(grade)
    await session.commit()
