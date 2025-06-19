from __future__ import annotations

import datetime
import logging
from uuid import UUID
from typing import Annotated
import os
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
from fastapi import APIRouter
from fastapi import Response, HTTPException
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, or_, func
from sqlalchemy.orm import selectinload
from io import BytesIO


from ..db import schemas, engine
from ..db import declaration
from ..db.declaration.user import User
from ..db.declaration.school import School, Class

router = APIRouter(tags=["Teacher"], prefix="/teacher")


@router.get("/statistics")
async def get_class_statistics(session: AsyncSession = Depends(engine.getSession)):
    from app.db.declaration.school import UserClassMark  # импортируем напрямую

    # Дисциплины, которые считаются пропусками
    absence_disciplines = {
        "Пропуск по уважительной причине",
        "Пропуск без уважительной причины",
        "Пропуск по болезни"
    }

    # Получаем все классы
    class_query = await session.execute(select(Class))
    classes = class_query.scalars().all()

    stats = []

    for cl in classes:
        # Запрос по всем предметам
        stmt = (
            select(
                UserClassMark.discipline,
                func.avg(UserClassMark.mark).label("average"),
                func.count(UserClassMark.mark).label("count")
            )
            .where(UserClassMark.class_uuid == cl.uuid)
            .group_by(UserClassMark.discipline)
        )
        result = await session.execute(stmt)

        discipline_stats = []
        absence_stats = []

        for row in result.all():
            if row.discipline in absence_disciplines:
                absence_stats.append({
                    "discipline": row.discipline,
                    "absences_count": row.count
                })
            else:
                discipline_stats.append({
                    "discipline": row.discipline,
                    "average_mark": round(row.average, 2),
                    "marks_count": row.count
                })

        stats.append({
            "class_uuid": str(cl.uuid),
            "class_name": cl.class_name,
            "start_year": cl.start_year,
            "school_uuid": str(cl.school_uuid),
            "disciplines": discipline_stats,
            "absences": absence_stats  # отдельное поле
        })

    return stats



@router.get("/plot_avg_distribution", response_class=Response)
async def plot_avg_distribution(session: AsyncSession = Depends(engine.getSession)):
    class_query = await session.execute(select(Class))
    classes = class_query.scalars().all()

    if not classes:
        return Response(status_code=404, content="Нет классов")

    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import math

    # plt.rcParams.update({
    #     'font.size': 30,  # базовый размер шрифта
    #     'axes.titlesize': 20,  # размер заголовков
    #     'axes.labelsize': 20,  # размер подписей осей (если есть)
    #     'xtick.labelsize': 20,
    #     'ytick.labelsize': 20,
    #     'legend.fontsize': 20
    # })

    fig, axs = plt.subplots(
        nrows=math.ceil(len(classes) / 2), ncols=2,
        figsize=(12, 6 * math.ceil(len(classes) / 2))
    )

    axs = axs.flatten() if isinstance(axs, np.ndarray) else [axs]

    for idx, cl in enumerate(classes):
        stmt = (
            select(User.uuid)
            .join(declaration.school.UserClassMark, User.uuid == declaration.school.UserClassMark.user_uuid)
            .where(declaration.school.UserClassMark.class_uuid == cl.uuid)
            .distinct()
        )
        result = await session.execute(stmt)
        students = result.scalars().all()

        # Собираем оценки по каждому ученику
        user_bins = defaultdict(list)
        for user_uuid in students:
            stmt = (
                select(declaration.school.UserClassMark.mark)
                .where(
                    declaration.school.UserClassMark.user_uuid == user_uuid,
                    declaration.school.UserClassMark.class_uuid == cl.uuid
                )
            )
            res = await session.execute(stmt)
            marks = res.scalars().all()
            if marks:
                avg = sum(marks) / len(marks)
                user_bins[user_uuid] = avg

        # Подсчитываем, сколько людей попадают в какие категории
        bins = {
            "≥ 4.5": 0,
            "≥ 3.5": 0,
            "≥ 2.5": 0,
            "< 2.5": 0
        }
        for avg in user_bins.values():
            if avg >= 4.5:
                bins["≥ 4.5"] += 1
            elif avg >= 3.5:
                bins["≥ 3.5"] += 1
            elif avg >= 2.5:
                bins["≥ 2.5"] += 1
            else:
                bins["< 2.5"] += 1

        # Удалим нулевые категории для красоты
        bins = {k: v for k, v in bins.items() if v > 0}

        ax = axs[idx]
        if bins:
            ax.pie(
                bins.values(),
                labels=bins.keys(),
                autopct="%1.1f%%",
                labeldistance=1.1
            )
            ax.set_title(f"{cl.class_name} ({cl.start_year})")

            # Добавляем подпись под пай-чартом
            ax.text(
                0, -1.3,  # координаты под диаграммой
                "Распределение учеников по среднему баллу",
                ha='center',
                va='center',
                fontsize=10
            )
        else:
            ax.axis('off')
            ax.set_title(f"{cl.class_name} ({cl.start_year}) — нет данных")

    for i in range(len(classes), len(axs)):
        axs[i].axis('off')

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")
