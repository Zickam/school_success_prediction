from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...db.engine import getSession
from ...db.declaration import School
from ...db.schemas.school import SchoolCreate, SchoolUpdate, School as SchoolSchema

router = APIRouter()

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
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(School).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{school_id}", response_model=SchoolSchema)
async def get_school(
    school_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(School).where(School.uuid == school_id))
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
    result = await session.execute(select(School).where(School.uuid == school_id))
    school = result.scalar_one_or_none()
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    
    for field, value in school_update.model_dump(exclude_unset=True).items():
        setattr(school, field, value)
    
    await session.commit()
    await session.refresh(school)
    return school

@router.delete("/{school_id}", status_code=204)
async def delete_school(
    school_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(select(School).where(School.uuid == school_id))
    school = result.scalar_one_or_none()
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    
    await session.delete(school)
    await session.commit() 