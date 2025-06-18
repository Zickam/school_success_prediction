from __future__ import annotations

import datetime
import logging
from uuid import UUID
from typing import Annotated
import os
from collections import defaultdict
from io import BytesIO

import matplotlib.pyplot as plt
from fastapi import APIRouter, Query
from fastapi import Response, HTTPException
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, or_, not_

from ..db.declaration.school import UserClassMark
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


@router.get("/predict_success")
async def predict_success(
    user_uuid: UUID | None = Query(default=None),
    chat_id: int | None = Query(default=None),
    session: AsyncSession = Depends(engine.getSession)
):
    if not user_uuid and not chat_id:
        return {"error": "user_uuid or chat_id is required"}

    stmt = select(UserClassMark.mark).join(User).where(
        or_(
            User.uuid == user_uuid if user_uuid else False,
            User.chat_id == chat_id if chat_id else False
        )
    )

    result = await session.execute(stmt)
    marks = result.scalars().all()

    if not marks:
        return {
            "status": "unknown",
            "confidence": 0.0,
            "message": "У ученика нет оценок, невозможно сделать прогноз."
        }

    # --- ТУПАЯ ЛОГИКА АНАЛИЗА ---
    count_total = len(marks)
    count_failing = len([m for m in marks if m <= 3])

    # Простая эвристика:
    if count_failing == 0:
        level = "успешный"
        confidence = 0.95
    elif count_failing <= 2:
        level = "успешный"
        confidence = 0.75
    elif count_failing <= count_total // 2:
        level = "неуспешный"
        confidence = 0.4
    else:
        level = "неуспешный"
        confidence = 0.2

    return {
        "status": level,
        "confidence": round(confidence, 2),
        "total_marks": count_total,
        "bad_marks": count_failing,
        "message": f"Оценок всего: {count_total}, из них 'троек и ниже': {count_failing}"
    }


@router.get("/plot_progression", response_class=Response)
async def plot_user_progression(
    user_uuid: UUID = Query(default=None),
    chat_id: int = Query(default=None),
    session: AsyncSession = Depends(engine.getSession)
):
    if not user_uuid and not chat_id:
        return Response(status_code=400, content="Provide user_uuid or chat_id")

    stmt = (
        select(UserClassMark.discipline, UserClassMark.mark, UserClassMark.created_at)
        .join(UserClassMark.user)
        .where(
            or_(
                User.uuid == user_uuid if user_uuid else False,
                User.chat_id == chat_id if chat_id else False
            )
        )
    )
    result = await session.execute(stmt)
    data = result.all()

    if not data:
        return Response(status_code=404, content="No marks found for this user")

    from collections import defaultdict
    import matplotlib.pyplot as plt
    from io import BytesIO

    # Step 1: Build subject -> list of (year, month, avg_mark)
    subject_monthly_avg = defaultdict(lambda: defaultdict(list))
    for discipline, mark, created_at in data:
        if not created_at:
            continue
        year = created_at.year
        month = created_at.month
        subject_monthly_avg[discipline][(year, month)].append(mark)

    subject_points = {}
    for subject, month_dict in subject_monthly_avg.items():
        month_avg_list = []
        for (year, month), marks in month_dict.items():
            avg = sum(marks) / len(marks)
            month_avg_list.append((year, month, avg))
        subject_points[subject] = sorted(month_avg_list, key=lambda x: (x[0], x[1]))

    # Step 2: Extract all unique month labels across subjects
    all_months = sorted({(y, m) for pts in subject_points.values() for (y, m, _) in pts})
    month_labels = [f"{y}-M{str(m).zfill(2)}" for (y, m) in all_months]

    # Step 3: Plot
    plt.figure(figsize=(10, 6))
    for subject, records in subject_points.items():
        months = [f"{y}-M{str(m).zfill(2)}" for (y, m, _) in records]
        marks = [mark for _, _, mark in records]
        plt.plot(months, marks, marker='o', label=subject)

    plt.xlabel('Month')
    plt.ylabel('Average Mark')
    plt.title('Average Marks per Month for Each Subject')
    plt.xticks(rotation=45)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


@router.get("/plot_subject_averages", response_class=Response)
async def plot_subject_averages(
    user_uuid: UUID = Query(default=None),
    chat_id: int = Query(default=None),
    session: AsyncSession = Depends(engine.getSession)
):
    if not user_uuid and not chat_id:
        return Response(status_code=400, content="Provide user_uuid or chat_id")

    stmt = (
        select(UserClassMark.discipline, UserClassMark.mark)
        .join(UserClassMark.user)
        .where(
            or_(
                User.uuid == user_uuid if user_uuid else False,
                User.chat_id == chat_id if chat_id else False
            )
        )
    )
    result = await session.execute(stmt)
    data = result.all()

    if not data:
        return Response(status_code=404, content="No marks found for this user")

    # Подсчёт средней оценки по каждому предмету
    subject_marks = defaultdict(list)
    for discipline, mark in data:
        subject_marks[discipline].append(mark)

    subjects = list(subject_marks.keys())
    averages = [sum(marks) / len(marks) for marks in subject_marks.values()]

    # Построение графика
    plt.figure(figsize=(10, 6))
    bars = plt.bar(subjects, averages)
    plt.ylabel("Средняя оценка")
    plt.title("Средняя оценка по каждому предмету")
    plt.ylim(1, 5.5)
    plt.xticks(rotation=45)
    plt.grid(axis='y')

    # Добавление значений над столбиками
    for bar, avg in zip(bars, averages):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, f"{avg:.1f}", ha='center', va='bottom')

    plt.tight_layout()

    # Отправка как изображения
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")
