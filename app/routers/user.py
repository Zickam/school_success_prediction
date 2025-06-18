from __future__ import annotations

import datetime
import logging
from uuid import UUID
from typing import Annotated
import os

from fastapi import APIRouter
from fastapi import Response, HTTPException
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, or_, not_

from ..db import schemas, engine
from ..db import declaration
from ..db.declaration.school import Class
from ..db.declaration.user import User

router = APIRouter(tags=["User"], prefix="/user")


@router.get("", responses={404: {}}, response_model=schemas.user.UserRead)
async def getUser(
    chat_id: int | None = None,
    user_uuid: UUID | None = None,
    session: AsyncSession = Depends(engine.getSession)
):
    filters = []
    if chat_id is not None:
        filters.append(User.chat_id == chat_id)
    if user_uuid is not None:
        filters.append(User.uuid == user_uuid)

    if not filters:
        return Response(status_code=400, content="Missing query params")

    query = select(User).where(or_(*filters))
    result = await session.execute(query)
    users = result.scalars().all()

    if len(users) == 1:
        return users[0]
    elif users:
        return Response(status_code=409, content="Multiple users found")

    return Response(status_code=404, content="User not found")


@router.post("", response_model=schemas.user.UserRead, responses={404: {}})
async def createUser(
    user: Annotated[schemas.user.UserCreate, Depends()],
    session: AsyncSession = Depends(engine.getSession)
):
    result = await session.execute(select(User).where(User.chat_id.isnot(None) & (User.chat_id == user.chat_id)))
    users = result.scalars().all()
    if len(users) > 0:
        return Response(status_code=409, content="User with such chat_id already exists")

    new_user = declaration.user.User(**user.model_dump(exclude_unset=False))
    session.add(new_user)
    await session.commit()

    return new_user


@router.get("/class", response_model=schemas.school.ClassRead, responses={404: {}})
async def getUserClass(
    user_uuid: UUID = None,
    chat_id: int = None,
    session: AsyncSession = Depends(engine.getSession)
):
    if user_uuid is None:
        user = await getUser(chat_id=chat_id, session=session)
        user_uuid = user.uuid

    logging.info(user_uuid)
    query = select(Class).join(Class.users).where(
        or_(
            User.uuid == user_uuid if user_uuid is not None else False,
            User.chat_id == chat_id if chat_id is not None else False
        )
    )
    result = await session.execute(query)
    classes = result.scalars().all()

    if not classes:
        raise HTTPException(status_code=404, detail="No class found for this user")

    return classes[0]
