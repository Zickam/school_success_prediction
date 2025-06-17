from __future__ import annotations

import datetime
import logging
from uuid import UUID
from typing import Annotated, List
import os

from fastapi import APIRouter, Response, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, or_, not_

from ..db import schemas, engine
from ..db.models import User, Class, School
from ..db.schemas.user import UserCreate, UserUpdate, UserResponse, Roles
from ..db.engine import getSession
from ..auth_dependency import require_auth

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0, limit: int = 100, session: AsyncSession = Depends(getSession)
):

    result = await session.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate, session: AsyncSession = Depends(getSession)
):

    if user_data.class_uuid:
        result = await session.execute(
            select(Class).where(Class.uuid == user_data.class_uuid)
        )
        class_ = result.scalar_one_or_none()
        if not class_:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Class not found"
            )

    if user_data.school_uuid:
        result = await session.execute(
            select(School).where(School.uuid == user_data.school_uuid)
        )
        school = result.scalar_one_or_none()
        if not school:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="School not found"
            )

    user = User(**user_data.model_dump())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, session: AsyncSession = Depends(getSession)):

    result = await session.execute(select(User).where(User.uuid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID, user_data: UserUpdate, session: AsyncSession = Depends(getSession)
):

    result = await session.execute(select(User).where(User.uuid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_data.class_uuid:
        result = await session.execute(
            select(Class).where(Class.uuid == user_data.class_uuid)
        )
        class_ = result.scalar_one_or_none()
        if not class_:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Class not found"
            )

    if user_data.school_uuid:
        result = await session.execute(
            select(School).where(School.uuid == user_data.school_uuid)
        )
        school = result.scalar_one_or_none()
        if not school:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="School not found"
            )

    for key, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, session: AsyncSession = Depends(getSession)):

    result = await session.execute(select(User).where(User.uuid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await session.delete(user)
    await session.commit()


@router.get("/by_chat_id", responses={404: {}}, response_model=UserResponse)
async def get_user_by_id(
    chat_id: int | None = None,
    user_uuid: UUID | None = None,
    session: AsyncSession = Depends(getSession),
):
    filters = []
    if chat_id is not None:
        filters.append(User.chat_id == chat_id)
    if user_uuid is not None:
        filters.append(User.uuid == user_uuid)

    if not filters:
        raise HTTPException(status_code=400, detail="Missing query params")

    query = select(User).where(or_(*filters))
    result = await session.execute(query)
    users = result.scalars().all()

    if len(users) == 1:
        return users[0]
    elif users:
        raise HTTPException(status_code=409, detail="Multiple users found")

    raise HTTPException(status_code=404, detail="User not found")


@router.post("", response_model=UserResponse)
async def create_user_by_id(
    user: UserCreate, session: AsyncSession = Depends(getSession)
):
    try:
        result = await session.execute(select(User).where(User.chat_id == user.chat_id))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=409, detail="User with such chat_id already exists"
            )

        new_user = User(**user.model_dump())
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        return new_user
    except Exception as e:
        await session.rollback()
        logging.error(f"Failed to create user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
