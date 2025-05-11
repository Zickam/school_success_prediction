from __future__ import annotations
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ...db.engine import getSession
from ...db.models import Class, User
from ...db.schemas.class_ import ClassCreate, ClassUpdate, ClassResponse as ClassSchema
from ...db.schemas.user import User as UserSchema, Roles
from ...policy import PolicyManager

router = APIRouter(tags=["Class"], prefix="/classes")

@router.post("/", response_model=ClassSchema)
async def create_class(
    class_: ClassCreate,
    session: AsyncSession = Depends(getSession)
):
    db_class = Class(**class_.model_dump())
    session.add(db_class)
    await session.commit()
    await session.refresh(db_class)
    return db_class

@router.get("/", response_model=List[ClassSchema])
async def get_classes(
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Class))
    classes = result.scalars().all()
    return classes

@router.get("/{class_id}", response_model=ClassSchema)
async def get_class(
    class_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(Class).where(Class.uuid == class_id)
    )
    class_ = result.scalar_one_or_none()
    if class_ is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_

@router.put("/{class_id}", response_model=ClassSchema)
async def update_class(
    class_id: UUID,
    class_update: ClassUpdate,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(Class).where(Class.uuid == class_id)
    )
    class_ = result.scalar_one_or_none()
    if class_ is None:
        raise HTTPException(status_code=404, detail="Class not found")

    for field, value in class_update.model_dump(exclude_unset=True).items():
        setattr(class_, field, value)

    await session.commit()
    await session.refresh(class_)
    return class_

@router.delete("/{class_id}")
async def delete_class(
    class_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(Class).where(Class.uuid == class_id)
    )
    class_ = result.scalar_one_or_none()
    if class_ is None:
        raise HTTPException(status_code=404, detail="Class not found")

    await session.delete(class_)
    await session.commit()
    return {"message": "Class deleted successfully"}

@router.get("/{class_id}/students", response_model=List[UserSchema])
async def get_class_students(
    class_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(Class).options(selectinload(Class.users)).where(Class.uuid == class_id)
    )
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return [user for user in class_.users if user.role == Roles.student]

@router.get("/{class_id}/teachers", response_model=List[UserSchema])
async def get_class_teachers(
    class_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(Class).options(selectinload(Class.users)).where(Class.uuid == class_id)
    )
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return [user for user in class_.users if user.role == Roles.teacher]

@router.post("/{class_id}/join", response_model=ClassSchema)
async def join_class(
    class_id: UUID,
    user_uuid: UUID,
    session: AsyncSession = Depends(getSession)
):
    # Get user
    result = await session.execute(
        select(User).options(selectinload(User.classes)).where(User.uuid == user_uuid)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get class
    result = await session.execute(select(Class).where(Class.uuid == class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")

    # Check if user is already in the class
    if class_ in user.classes:
        raise HTTPException(status_code=409, detail="User already in this class")

    # Add user to class
    user.classes.append(class_)
    await session.commit()
    await session.refresh(class_)
    return class_ 