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

