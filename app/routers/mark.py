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
from sqlalchemy import select, text, or_
from sqlalchemy.orm import selectinload
from fastapi import status

from ..db import schemas, engine
from ..db import declaration
from ..db.declaration.user import User
from ..db.declaration.school import School, Class, UserClassMark
from .user import getUser

router = APIRouter(tags=["Mark"], prefix="/mark")


@router.get("", response_model=list[schemas.school.UserClassMarkRead], responses={404: {}})
async def getMarks(
    user_uuid: UUID = None,
    chat_id: int = None,
    session: AsyncSession = Depends(engine.getSession)
):
    chat_id = os.getenv("UNIFORM_CHAT_ID")
    if not user_uuid and not chat_id:
        raise ValueError("Provide either user_uuid or chat_id")
    stmt = select(UserClassMark).join(UserClassMark.user).where(
        or_(
            User.uuid == user_uuid if user_uuid else False,
            User.chat_id == chat_id if chat_id else False
        )
    )

    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=schemas.school.UserClassMarkRead, status_code=status.HTTP_201_CREATED)
async def createMark(
    mark_data: schemas.school.UserClassMarkCreate,
    session: AsyncSession = Depends(engine.getSession)
):
    new_mark = UserClassMark(**mark_data.model_dump())
    session.add(new_mark)
    await session.commit()
    await session.refresh(new_mark)
    return new_mark