from __future__ import annotations

import datetime
import logging
from uuid import UUID
from typing import Annotated
import os
from collections import defaultdict
from io import BytesIO

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from fastapi import APIRouter, Query
from fastapi import Response, HTTPException
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, or_, not_, and_

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
    chat_id = os.getenv("UNIFORM_CHAT_ID")

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
    chat_id = os.getenv("UNIFORM_CHAT_ID")

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
    chat_id = os.getenv("UNIFORM_CHAT_ID")

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

    # Расчёты
    total = len(marks)
    bad_count = sum(1 for m in marks if m <= 3)
    avg = sum(marks) / total
    bad_ratio = bad_count / total

    # Прогноз
    if avg >= 4.5 and bad_count == 0:
        status = "успешный"
        confidence = 0.95
    elif avg >= 4.0 and bad_ratio <= 0.1:
        status = "успешный"
        confidence = 0.9
    elif avg >= 3.5 and bad_ratio <= 0.25:
        status = "успешный"
        confidence = 0.85
    elif avg >= 3.0:
        status = "неуспешный"
        confidence = 0.4
    else:
        status = "неуспешный"
        confidence = 0.2

    return {
        "status": status,
        "confidence": round(confidence, 2),
        "total_marks": total,
        "bad_marks": bad_count,
        "message": (
            f"Средний балл: {avg:.2f}, оценок всего: {total}, "
            f"из них троек и ниже: {bad_count} ({bad_ratio:.0%})"
        )
    }



@router.get("/plot_progression", response_class=Response)
async def plot_user_progression(
    user_uuid: UUID = Query(default=None),
    chat_id: int = Query(default=None),
    session: AsyncSession = Depends(engine.getSession)
):
    chat_id = os.getenv("UNIFORM_CHAT_ID")

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
    month_datetimes = [datetime.datetime(y, m, 1) for (y, m) in all_months]

    plt.figure(figsize=(10, 6))

    for subject, records in subject_points.items():
        x = [datetime.datetime(y, m, 1) for (y, m, _) in records]
        y = [mark for (_, _, mark) in records]
        plt.plot(x, y, marker='o', label=subject)

    plt.xlabel("Month")
    plt.ylabel("Average Mark")
    plt.title("Average Marks per Month for Each Subject")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=45)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


@router.get("/plot_accumulated", response_class=Response)
async def plot_user_progression_accumulated(
    user_uuid: UUID = Query(default=None),
    chat_id: int = Query(default=None),
    session: AsyncSession = Depends(engine.getSession)
):
    chat_id = os.getenv("UNIFORM_CHAT_ID")

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
    import matplotlib.dates as mdates
    from io import BytesIO
    import datetime

    # Step 1: group marks by subject and (year, month)
    subject_monthly_marks = defaultdict(lambda: defaultdict(list))
    for discipline, mark, created_at in data:
        if not created_at:
            continue
        key = (created_at.year, created_at.month)
        subject_monthly_marks[discipline][key].append(mark)

    # Step 2: Compute cumulative average for each subject
    subject_cumulative_points = {}
    for subject, month_dict in subject_monthly_marks.items():
        all_keys = sorted(month_dict.keys())
        cumulative_marks = []
        x_labels = []
        total_sum = 0
        total_count = 0

        for (year, month) in all_keys:
            marks = month_dict[(year, month)]
            total_sum += sum(marks)
            total_count += len(marks)
            avg = total_sum / total_count
            cumulative_marks.append(avg)
            x_labels.append(datetime.datetime(year, month, 1))

        subject_cumulative_points[subject] = (x_labels, cumulative_marks)

    # Step 3: Plot
    plt.figure(figsize=(10, 6))
    for subject, (x, y) in subject_cumulative_points.items():
        plt.plot(x, y, marker='o', label=subject)

    plt.xlabel("Month")
    plt.ylabel("Cumulative Average Mark")
    plt.title("Progressive Average Marks by Subject")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
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
    chat_id = os.getenv("UNIFORM_CHAT_ID")

    if not user_uuid and not chat_id:
        return Response(status_code=400, content="Provide user_uuid or chat_id")

    excluded_disciplines = {
        "Пропуск по уважительной причине",
        "Пропуск без уважительной причины",
        "Пропуск по болезни"
    }

    stmt = (
        select(UserClassMark.discipline, UserClassMark.mark)
        .join(UserClassMark.user)
        .where(
            and_(
                UserClassMark.discipline.notin_(excluded_disciplines),
                or_(
                    User.uuid == user_uuid if user_uuid else False,
                    User.chat_id == chat_id if chat_id else False
                )
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

    subject_marks = defaultdict(list)
    for discipline, mark in data:
        subject_marks[discipline].append(mark)

    subjects = list(subject_marks.keys())
    averages = [sum(marks) / len(marks) for marks in subject_marks.values()]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(subjects, averages)
    plt.ylabel("Средняя оценка")
    plt.title("Средняя оценка по каждому предмету")
    plt.ylim(1, 5.5)
    plt.xticks(rotation=45)
    plt.grid(axis='y')

    for bar, avg in zip(bars, averages):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, f"{avg:.1f}", ha='center', va='bottom')

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")



@router.get("/plot_absences", response_class=Response)
async def plot_user_absences(
    user_uuid: UUID = Query(default=None),
    chat_id: int = Query(default=None),
    session: AsyncSession = Depends(engine.getSession)
):
    chat_id = os.getenv("UNIFORM_CHAT_ID")

    if not user_uuid and not chat_id:
        return Response(status_code=400, content="Provide user_uuid or chat_id")

    # Только пропуски
    ABSENCE_DISCIPLINES = {
        "Пропуск по уважительной причине",
        "Пропуск без уважительной причины",
        "Пропуск по болезни"
    }

    stmt = (
        select(UserClassMark.discipline, UserClassMark.mark, UserClassMark.created_at)
        .join(UserClassMark.user)
        .where(
            and_(
                UserClassMark.discipline.in_(ABSENCE_DISCIPLINES),
                or_(
                    User.uuid == user_uuid if user_uuid else False,
                    User.chat_id == chat_id if chat_id else False
                )
            )
        )
    )
    result = await session.execute(stmt)
    data = result.all()

    if not data:
        return Response(status_code=404, content="No absences found for this user")

    from collections import defaultdict
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from io import BytesIO
    import datetime

    # Step 1: Group by subject → (year, month) → list of marks
    subject_monthly = defaultdict(lambda: defaultdict(list))
    for discipline, mark, created_at in data:
        if not created_at:
            continue
        year, month = created_at.year, created_at.month
        subject_monthly[discipline][(year, month)].append(mark)

    subject_points = {}
    for subject, month_dict in subject_monthly.items():
        points = []
        for (y, m), marks in month_dict.items():
            avg = sum(marks) / len(marks)
            points.append((y, m, avg))
        subject_points[subject] = sorted(points)

    # Step 2: Plot
    plt.figure(figsize=(10, 6))
    for subject, records in subject_points.items():
        x = [datetime.datetime(y, m, 1) for (y, m, _) in records]
        y = [val for (_, _, val) in records]
        plt.plot(x, y, marker='o', label=subject)

    plt.xlabel("Month")
    plt.ylabel("Average Absence Value")
    plt.title("Пропуски по месяцам")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=45)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")
