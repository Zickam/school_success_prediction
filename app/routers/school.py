from __future__ import annotations
import os
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..db.engine import getSession
from ..db.declaration import School, Class, Subject, Grade, User
from ..db.schemas.school import (
    SchoolCreate, SchoolUpdate, School as SchoolSchema,
    ClassCreate, ClassUpdate, Class as ClassSchema,
    SubjectCreate, SubjectUpdate, Subject as SubjectSchema,
    GradeCreate, GradeUpdate, Grade as GradeSchema
)
from ..db.schemas.user import User as UserSchema, Roles
from ..policy import PolicyManager

router = APIRouter(
    prefix="/schools",
    tags=["schools"]
)


@router.post("/", response_model=SchoolSchema)
async def create_school(
    school: SchoolCreate,
    session: AsyncSession = Depends(getSession)
):
    db_school = School(**school.model_dump())
    session.add(db_school)
    await session.commit()
    await session.refresh(db_school)
    return db_school


@router.get("/", response_model=List[SchoolSchema])
async def get_schools(
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(School))
    schools = result.scalars().all()
    return schools


@router.get("/{school_id}", response_model=SchoolSchema)
async def get_school(
    school_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(School).where(School.uuid == school_id)
    )
    school = result.scalar_one_or_none()
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@router.put("/{school_id}", response_model=SchoolSchema)
async def update_school(
    school_id: UUID,
    school_update: SchoolUpdate,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(School).where(School.uuid == school_id)
    )
    school = result.scalar_one_or_none()
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    
    for field, value in school_update.model_dump(exclude_unset=True).items():
        setattr(school, field, value)
    
    await session.commit()
    await session.refresh(school)
    return school


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school(
    school_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(School).where(School.uuid == school_id)
    )
    school = result.scalar_one_or_none()
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    
    await session.delete(school)
    await session.commit()
    return {"message": "School deleted successfully"}


@router.post("/classes/", response_model=ClassSchema)
async def create_class(
    class_: ClassCreate,
    session: AsyncSession = Depends(getSession)
):
    db_class = Class(**class_.model_dump())
    session.add(db_class)
    await session.commit()
    await session.refresh(db_class)
    return db_class


@router.get("/classes/", response_model=List[ClassSchema])
async def get_classes(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Class).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/classes/{class_id}", response_model=ClassSchema)
async def get_class(
    class_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Class).where(Class.uuid == class_id))
    class_ = result.scalar_one_or_none()
    if class_ is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_


@router.put("/classes/{class_id}", response_model=ClassSchema)
async def update_class(
    class_id: UUID,
    class_update: ClassUpdate,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Class).where(Class.uuid == class_id))
    class_ = result.scalar_one_or_none()
    if class_ is None:
        raise HTTPException(status_code=404, detail="Class not found")
    
    for field, value in class_update.model_dump(exclude_unset=True).items():
        setattr(class_, field, value)
    
    await session.commit()
    await session.refresh(class_)
    return class_


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Class).where(Class.uuid == class_id))
    class_ = result.scalar_one_or_none()
    if class_ is None:
        raise HTTPException(status_code=404, detail="Class not found")
    
    await session.delete(class_)
    await session.commit()


@router.post("/classes/{class_id}/join", response_model=ClassSchema)
async def join_class(
    class_id: UUID,
    user_uuid: UUID,
    session: AsyncSession = Depends(getSession)
):
    # Get user
    result = await session.execute(
        select(User).options(selectinload(User.classes)).where(User.uuid == user_uuid)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get class
    result = await session.execute(select(Class).where(Class.uuid == class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")

    # Check if user is already in the class
    if class_ in user.classes:
        raise HTTPException(status_code=409, detail="User already in this class")

    # Add user to class
    user.classes.append(class_)
    await session.commit()
    await session.refresh(class_)
    return class_


@router.get("/classes/{class_id}/students", response_model=List[UserSchema])
async def get_class_students(
    class_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(Class).options(selectinload(Class.users)).where(Class.uuid == class_id)
    )
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return [user for user in class_.users if user.role == Roles.student]


@router.get("/classes/{class_id}/teachers", response_model=List[UserSchema])
async def get_class_teachers(
    class_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(Class).options(selectinload(Class.users)).where(Class.uuid == class_id)
    )
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return [user for user in class_.users if user.role == Roles.teacher]


@router.get("/users/{user_uuid}/grades", response_model=List[GradeSchema])
async def get_user_grades(
    user_uuid: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(Grade).where(Grade.user_uuid == user_uuid)
    )
    return result.scalars().all()


@router.get("/users/{user_uuid}/classes", response_model=List[ClassSchema])
async def get_user_classes(
    user_uuid: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(User).options(selectinload(User.classes)).where(User.uuid == user_uuid)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.classes


@router.post("/subjects/", response_model=SubjectSchema)
async def create_subject(
    subject: SubjectCreate,
    session: AsyncSession = Depends(getSession)
):
    db_subject = Subject(**subject.model_dump())
    session.add(db_subject)
    await session.commit()
    await session.refresh(db_subject)
    return db_subject


@router.get("/subjects/", response_model=List[SubjectSchema])
async def get_subjects(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Subject).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/subjects/{subject_id}", response_model=SubjectSchema)
async def get_subject(
    subject_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Subject).where(Subject.uuid == subject_id))
    subject = result.scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.put("/subjects/{subject_id}", response_model=SubjectSchema)
async def update_subject(
    subject_id: UUID,
    subject_update: SubjectUpdate,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Subject).where(Subject.uuid == subject_id))
    subject = result.scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    for field, value in subject_update.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    
    await session.commit()
    await session.refresh(subject)
    return subject


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Subject).where(Subject.uuid == subject_id))
    subject = result.scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    await session.delete(subject)
    await session.commit()


@router.post("/grades/", response_model=GradeSchema)
async def create_grade(
    grade: GradeCreate,
    session: AsyncSession = Depends(getSession)
):
    db_grade = Grade(**grade.model_dump())
    session.add(db_grade)
    await session.commit()
    await session.refresh(db_grade)
    return db_grade


@router.get("/grades/", response_model=List[GradeSchema])
async def get_grades(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Grade).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/grades/{grade_id}", response_model=GradeSchema)
async def get_grade(
    grade_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Grade).where(Grade.uuid == grade_id))
    grade = result.scalar_one_or_none()
    if grade is None:
        raise HTTPException(status_code=404, detail="Grade not found")
    return grade


@router.put("/grades/{grade_id}", response_model=GradeSchema)
async def update_grade(
    grade_id: UUID,
    grade_update: GradeUpdate,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Grade).where(Grade.uuid == grade_id))
    grade = result.scalar_one_or_none()
    if grade is None:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    for field, value in grade_update.model_dump(exclude_unset=True).items():
        setattr(grade, field, value)
    
    await session.commit()
    await session.refresh(grade)
    return grade


@router.delete("/grades/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grade(
    grade_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(Grade).where(Grade.uuid == grade_id))
    grade = result.scalar_one_or_none()
    if grade is None:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    await session.delete(grade)
    await session.commit()