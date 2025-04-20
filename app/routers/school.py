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

from ..db import schemas, engine
from ..db import declaration
from ..db.declaration.user import User
from ..db.declaration.school import School, Class

router = APIRouter(tags=["School"], prefix="/school")


@router.get("", response_model=schemas.school.SchoolRead, responses={404: {}})
async def getSchool(
    school: Annotated[schemas.school.SchoolRead, Depends()],
    session: AsyncSession = Depends(engine.getSession)
):
    query = select(School).where(School.uuid == school.uuid)
    result = await session.execute(query)
    schools = result.scalars().all()

    if len(schools) == 1:
        return schools[0]
    elif len(schools) > 1:
        return Response(status_code=400, content="*Impossible*: more than 1 schools with the same uuid")

    query = select(School).where(School.facility_name == school.facility_name)
    result = await session.execute(query)
    schools = result.scalars().all()

    if len(schools) == 1:
        return schools[0]
    elif len(schools) > 1:
        return Response(status_code=400, content="*Impossible*: more than 1 schools with the same facility name")

    return Response(status_code=404, content="School not found")


@router.post("", response_model=schemas.school.SchoolRead, responses={404: {}})
async def createSchool(
    school: Annotated[schemas.school.SchoolCreate, Depends()],
    session: AsyncSession = Depends(engine.getSession)
):
    result = await session.execute(select(School).where(School.facility_name == school.facility_name))
    users = result.scalars().all()
    if len(users) > 0:
        return Response(status_code=409, content="School with such facility_name already exists")

    new_school = declaration.school.School(**school.model_dump(exclude_unset=False))
    session.add(new_school)
    await session.commit()

    return new_school


@router.get("/class", response_model=schemas.school.ClassRead, responses={404: {}})
async def getClass(
    uuid: UUID | None = None,
    session: AsyncSession = Depends(engine.getSession)
):
    query = select(Class).where(Class.uuid == uuid)
    result = await session.execute(query)
    users = result.scalars().all()

    if len(users) == 1:
        return users[0]
    elif len(users) > 1:
        return Response(status_code=400, content="*Impossible*: more than 1 schools with the same uuid")

    return Response(status_code=404, content="Class not found")


@router.post("/class", response_model=schemas.school.ClassRead, responses={404: {}})
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


