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
from sqlalchemy import select, text, or_, func
from sqlalchemy.orm import selectinload

from ..db import schemas, engine
from ..db import declaration
from ..db.declaration.user import User
from ..db.declaration.school import School, Class

router = APIRouter(tags=["Teacher"], prefix="/teacher")


@router.get("/statistics")
async def get_class_statistics(session: AsyncSession = Depends(engine.getSession)):
    # Query all class UUIDs with names
    class_query = await session.execute(select(Class))
    classes = class_query.scalars().all()

    stats = []

    for cl in classes:
        # For each class, calculate average and count per discipline
        stmt = (
            select(
                declaration.school.UserClassMark.discipline,
                func.avg(declaration.school.UserClassMark.mark).label("average"),
                func.count(declaration.school.UserClassMark.mark).label("count")
            )
            .where(declaration.school.UserClassMark.class_uuid == cl.uuid)
            .group_by(declaration.school.UserClassMark.discipline)
        )

        result = await session.execute(stmt)
        discipline_stats = [
            {
                "discipline": row.discipline,
                "average_mark": round(row.average, 2),
                "marks_count": row.count
            }
            for row in result.all()
        ]

        stats.append({
            "class_uuid": str(cl.uuid),
            "class_name": cl.class_name,
            "start_year": cl.start_year,
            "school_uuid": str(cl.school_uuid),
            "disciplines": discipline_stats
        })

    return stats