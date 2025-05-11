from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.engine import getSession
from app.db.models import Subject, User
from app.db.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse
from app.db.schemas.user import Roles
from app.auth_dependency import require_auth

router = APIRouter(
    prefix="/subjects",
    tags=["subjects"],
    # dependencies=[Depends(require_auth)]
)

@router.get("/", response_model=List[SubjectResponse])
async def get_subjects(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(getSession)
):
    """Get all subjects"""
    result = await session.execute(select(Subject).offset(skip).limit(limit))
    subjects = result.scalars().all()
    return subjects

@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    session: AsyncSession = Depends(getSession)
):
    """Create a new subject"""
    # Verify teacher exists and is a teacher
    if subject_data.teacher_uuid:
        result = await session.execute(
            select(User).where(
                User.uuid == subject_data.teacher_uuid,
                User.role == Roles.teacher
            )
        )
        teacher = result.scalar_one_or_none()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher not found or not a teacher"
            )

    subject = Subject(**subject_data.model_dump())
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    # Add subject to teacher's subjects
    if subject_data.teacher_uuid:
        if not teacher.teacher_subjects:
            teacher.teacher_subjects = []
        teacher.teacher_subjects.append(subject)
        await session.commit()
        await session.refresh(teacher)

    return subject

@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    """Get a specific subject by ID"""
    result = await session.execute(select(Subject).where(Subject.uuid == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return subject

@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: UUID,
    subject_data: SubjectUpdate,
    session: AsyncSession = Depends(getSession)
):
    """Update a subject"""
    result = await session.execute(select(Subject).where(Subject.uuid == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )

    # Verify teacher if being updated
    if subject_data.teacher_uuid:
        result = await session.execute(
            select(User).where(
                User.uuid == subject_data.teacher_uuid,
                User.role == Roles.teacher
            )
        )
        teacher = result.scalar_one_or_none()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher not found or not a teacher"
            )

        # Update teacher's subjects
        if not teacher.teacher_subjects:
            teacher.teacher_subjects = []
        if subject not in teacher.teacher_subjects:
            teacher.teacher_subjects.append(subject)
        await session.commit()
        await session.refresh(teacher)

    for key, value in subject_data.model_dump(exclude_unset=True).items():
        if key != 'teacher_uuid':  # Skip this as we handle it separately
            setattr(subject, key, value)

    await session.commit()
    await session.refresh(subject)
    return subject

@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    """Delete a subject"""
    result = await session.execute(select(Subject).where(Subject.uuid == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )

    # Remove subject from teacher's subjects
    if subject.teacher:
        if subject in subject.teacher.teacher_subjects:
            subject.teacher.teacher_subjects.remove(subject)
        await session.commit()

    await session.delete(subject)
    await session.commit() 