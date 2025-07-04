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

from ..db import schemas, engine
from ..db import declaration
from ..db.declaration.user import User
from ..db.declaration.school import School, Class

router = APIRouter(tags=["Class"], prefix="/class")



@router.get("", response_model=schemas.school.ClassRead, responses={404: {}})
async def getClass(
    uuid: UUID | None,
    session: AsyncSession = Depends(engine.getSession)
):
    query = select(Class).where(Class.uuid == uuid)
    result = await session.execute(query)
    classes = result.scalars().all()

    if len(classes) == 1:
        return classes[0]
    elif len(classes) > 1:
        return Response(status_code=400, content="*Impossible*: more than 1 schools with the same uuid")

    return Response(status_code=404, content="Class not found")


@router.post("", response_model=schemas.school.ClassRead, responses={404: {}})
async def createClass(
    class_: Annotated[schemas.school.ClassCreate, Depends()],
    session: AsyncSession = Depends(engine.getSession)
):
    filters = (School.uuid == class_.school_uuid)
    result = await session.execute(select(School).where(filters))
    schools = result.scalars().all()
    if len(schools) == 0:
        return Response(status_code=409, content="School not found")

    filters = ((Class.start_year == class_.start_year) &
             (Class.class_name == class_.class_name) &
             (Class.school_uuid == class_.school_uuid))
    result = await session.execute(select(Class).where(filters))
    classes = result.scalars().all()
    if len(classes) > 0:
        return Response(status_code=409, content="Same class already exists")

    new_class = declaration.school.Class(**class_.model_dump(exclude_unset=False))
    session.add(new_class)
    await session.commit()

    return new_class


@router.get("/invite_link_tg", response_model=str, responses={404: {}})
async def getTGInviteLinkToClass(
    class_uuid: UUID | None,
    session: AsyncSession = Depends(engine.getSession)
):
    query = select(Class).where(Class.uuid == class_uuid)
    result = await session.execute(query)
    classes = result.scalars().all()

    if len(classes) != 1:
        return Response(status_code=400, content="Class not found or other problem!")

    return f"t.me/{os.getenv('BOT_URL')}?start={classes[0].uuid}"


@router.post("/student_join", response_model=schemas.school.ClassRead, responses={404: {}})
async def studentJoinClass(
    user_uuid: UUID,
    class_uuid: UUID,
    session: AsyncSession = Depends(engine.getSession)
):
    query = select(User).options(selectinload(User.classes)).where(User.uuid == user_uuid)
    user = (await session.execute(query)).scalars().first()
    if not user:
        return Response(status_code=404, content="User not found")

    class_ = (await session.execute(select(Class).where(Class.uuid == class_uuid))).scalars().first()
    if not class_:
        return Response(status_code=404, content="Class not found")

    if class_ in user.classes:
        return Response(status_code=409, content="User already in this class")

    user.classes.append(class_)  # this works now
    await session.commit()

    return class_