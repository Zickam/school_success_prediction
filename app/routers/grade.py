from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.engine import getSession
from app.db.declaration import Grade, User, Subject
from app.db.schemas.grade import GradeCreate, GradeUpdate, GradeResponse
from app.auth_dependency import require_auth

router = APIRouter(
    prefix="/grades",
    tags=["grades"],
    dependencies=[Depends(require_auth)]
)

@router.get("/", response_model=List[GradeResponse])
async def get_grades(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    session: AsyncSession = Depends(getSession)
):
    """Get all grades with optional filtering"""
    query = select(Grade)
    
    if student_id:
        query = query.where(Grade.student_id == student_id)
    if subject_id:
        query = query.where(Grade.subject_id == subject_id)
    
    result = await session.execute(query.offset(skip).limit(limit))
    grades = result.scalars().all()
    return grades

@router.post("/", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
async def create_grade(
    grade_data: GradeCreate,
    session: AsyncSession = Depends(getSession)
):
    """Create a new grade"""
    # Verify student exists
    result = await session.execute(
        select(User).where(
            User.id == grade_data.student_id,
            User.role == "student"
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student not found or not a student"
        )

    # Verify subject exists
    result = await session.execute(
        select(Subject).where(Subject.id == grade_data.subject_id)
    )
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject not found"
        )

    grade = Grade(**grade_data.model_dump())
    session.add(grade)
    await session.commit()
    await session.refresh(grade)
    return grade

@router.get("/{grade_id}", response_model=GradeResponse)
async def get_grade(
    grade_id: int,
    session: AsyncSession = Depends(getSession)
):
    """Get a specific grade by ID"""
    result = await session.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found"
        )
    return grade

@router.put("/{grade_id}", response_model=GradeResponse)
async def update_grade(
    grade_id: int,
    grade_data: GradeUpdate,
    session: AsyncSession = Depends(getSession)
):
    """Update a grade"""
    result = await session.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found"
        )

    # Verify student if being updated
    if grade_data.student_id:
        result = await session.execute(
            select(User).where(
                User.id == grade_data.student_id,
                User.role == "student"
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student not found or not a student"
            )

    # Verify subject if being updated
    if grade_data.subject_id:
        result = await session.execute(
            select(Subject).where(Subject.id == grade_data.subject_id)
        )
        subject = result.scalar_one_or_none()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject not found"
            )

    for key, value in grade_data.model_dump(exclude_unset=True).items():
        setattr(grade, key, value)

    await session.commit()
    await session.refresh(grade)
    return grade

@router.delete("/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grade(
    grade_id: int,
    session: AsyncSession = Depends(getSession)
):
    """Delete a grade"""
    result = await session.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found"
        )

    await session.delete(grade)
    await session.commit() 