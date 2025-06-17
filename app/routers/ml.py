from __future__ import annotations
from typing import List, Dict
from uuid import UUID
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..db.engine import getSession
from ..db.models import User, Class, Grade, Subject
from ..db.schemas.user import User as UserSchema, Roles
from pydantic import BaseModel

router = APIRouter(prefix="/ml", tags=["machine_learning"])


class UserStats(BaseModel):
    user_uuid: UUID
    user_name: str
    predicted_success_rate: float
    confidence: float
    risk_factors: List[str]


class ClassStats(BaseModel):
    class_uuid: UUID
    class_name: str
    average_success_rate: float
    at_risk_users: List[UserStats]
    top_performers: List[UserStats]


@router.get("/users/{user_uuid}/predictions", response_model=UserStats)
async def get_user_predictions(
    user_uuid: UUID, session: AsyncSession = Depends(getSession)
) -> UserStats:

    result = await session.execute(select(User).where(User.uuid == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != Roles.student:
        raise HTTPException(status_code=400, detail="User is not a student")

    result = await session.execute(select(Grade).where(Grade.user_uuid == user_uuid))
    grades = result.scalars().all()

    return UserStats(
        user_uuid=user.uuid,
        user_name=user.name,
        predicted_success_rate=0.75,
        confidence=0.85,
        risk_factors=["Low attendance", "Inconsistent grades"],
    )


@router.get("/classes/{class_uuid}/predictions", response_model=ClassStats)
async def get_class_predictions(
    class_uuid: UUID, session: AsyncSession = Depends(getSession)
) -> ClassStats:

    result = await session.execute(select(Class).where(Class.uuid == class_uuid))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")

    users = [user for user in class_.users if user.role == Roles.student]

    user_predictions = []
    for user in users:
        prediction = await get_user_predictions(user.uuid, session)
        user_predictions.append(prediction)

    return ClassStats(
        class_uuid=class_.uuid,
        class_name=class_.name,
        average_success_rate=sum(p.predicted_success_rate for p in user_predictions)
        / len(user_predictions),
        at_risk_users=[p for p in user_predictions if p.predicted_success_rate < 0.6],
        top_performers=[p for p in user_predictions if p.predicted_success_rate > 0.8],
    )


@router.get("/school/{school_uuid}/predictions")
async def get_school_predictions(
    school_uuid: UUID, session: AsyncSession = Depends(getSession)
):

    result = await session.execute(
        select(Class).where(Class.school_uuid == school_uuid)
    )
    classes = result.scalars().all()

    class_predictions = []
    for class_ in classes:
        prediction = await get_class_predictions(class_.uuid, session)
        class_predictions.append(prediction)

    return {
        "total_classes": len(class_predictions),
        "total_users": sum(
            len(p.at_risk_users) + len(p.top_performers) for p in class_predictions
        ),
        "at_risk_users": sum(len(p.at_risk_users) for p in class_predictions),
        "top_performers": sum(len(p.top_performers) for p in class_predictions),
        "average_success_rate": (
            sum(p.average_success_rate for p in class_predictions)
            / len(class_predictions)
            if class_predictions
            else 0
        ),
        "class_predictions": class_predictions,
    }
