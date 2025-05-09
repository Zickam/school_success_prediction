from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.engine import getSession
from app.db.declaration import Class, User
from app.db.schemas.class_ import ClassCreate, ClassUpdate, ClassResponse
from app.auth_dependency import require_auth

router = APIRouter(
    prefix="/classes",
    tags=["classes"],
    dependencies=[Depends(require_auth)]
)

@router.get("/", response_model=List[ClassResponse])
async def get_classes(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(getSession)
):
    """Get all classes"""
    result = await session.execute(select(Class).offset(skip).limit(limit))
    classes = result.scalars().all()
    return classes

@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    session: AsyncSession = Depends(getSession)
):
    """Create a new class"""
    # Verify homeroom teacher exists and is a homeroom teacher
    if class_data.homeroom_teacher_uuid:
        result = await session.execute(
            select(User).where(
                User.uuid == class_data.homeroom_teacher_uuid,
                User.role == "homeroom_teacher"
            )
        )
        teacher = result.scalar_one_or_none()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Homeroom teacher not found or not a homeroom teacher"
            )

    class_ = Class(**class_data.model_dump())
    session.add(class_)
    await session.commit()
    await session.refresh(class_)
    return class_

@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: int,
    session: AsyncSession = Depends(getSession)
):
    """Get a specific class by ID"""
    result = await session.execute(select(Class).where(Class.id == class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    return class_

@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: int,
    class_data: ClassUpdate,
    session: AsyncSession = Depends(getSession)
):
    """Update a class"""
    result = await session.execute(select(Class).where(Class.id == class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Verify homeroom teacher if being updated
    if class_data.homeroom_teacher_uuid:
        result = await session.execute(
            select(User).where(
                User.uuid == class_data.homeroom_teacher_uuid,
                User.role == "homeroom_teacher"
            )
        )
        teacher = result.scalar_one_or_none()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Homeroom teacher not found or not a homeroom teacher"
            )

    for key, value in class_data.model_dump(exclude_unset=True).items():
        setattr(class_, key, value)

    await session.commit()
    await session.refresh(class_)
    return class_

@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: int,
    session: AsyncSession = Depends(getSession)
):
    """Delete a class"""
    result = await session.execute(select(Class).where(Class.id == class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    await session.delete(class_)
    await session.commit() 