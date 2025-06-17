from __future__ import annotations
import os
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..db.engine import getSession
from ..db.models import School, User
from ..db.schemas.school import (
    SchoolCreate, SchoolUpdate, School as SchoolSchema
)
from ..db.schemas.user import Roles
from ..policy import PolicyManager
from ..auth_dependency import require_auth

router = APIRouter(
    prefix="/schools",
    tags=["schools"],
    # dependencies=[Depends(require_auth)]
)


@router.post("/", response_model=SchoolSchema, status_code=status.HTTP_201_CREATED)
async def create_school(
    school_data: SchoolCreate,
    session: AsyncSession = Depends(getSession)
):
    """Create a new school"""
    # Verify director exists and is a director
    if school_data.director_uuid:
        result = await session.execute(
            select(User).where(
                User.uuid == school_data.director_uuid,
                User.role == Roles.director
            )
        )
        director = result.scalar_one_or_none()
        if not director:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Director not found or not a director"
            )

    school = School(**school_data.model_dump())
    session.add(school)
    await session.commit()
    await session.refresh(school)

    # Set director if provided
    if school_data.director_uuid:
        director.managed_school_uuid = school.uuid
        await session.commit()
        await session.refresh(director)

    return school


@router.get("/", response_model=List[SchoolSchema])
async def get_schools(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(getSession)
):
    """Get all schools"""
    result = await session.execute(select(School).offset(skip).limit(limit))
    schools = result.scalars().all()
    return schools


@router.get("/{school_id}", response_model=SchoolSchema)
async def get_school(
    school_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    """Get a specific school by ID"""
    result = await session.execute(select(School).where(School.uuid == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    return school


@router.put("/{school_id}", response_model=SchoolSchema)
async def update_school(
    school_id: UUID,
    school_data: SchoolUpdate,
    session: AsyncSession = Depends(getSession)
):
    """Update a school"""
    result = await session.execute(select(School).where(School.uuid == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )

    # Verify director if being updated
    if school_data.director_uuid:
        result = await session.execute(
            select(User).where(
                User.uuid == school_data.director_uuid,
                User.role == Roles.director
            )
        )
        director = result.scalar_one_or_none()
        if not director:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Director not found or not a director"
            )

        # Update director
        director.managed_school_uuid = school.uuid
        await session.commit()
        await session.refresh(director)

    for key, value in school_data.model_dump(exclude_unset=True).items():
        if key != 'director_uuid':  # Skip this as we handle it separately
            setattr(school, key, value)

    await session.commit()
    await session.refresh(school)
    return school


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school(
    school_id: UUID,
    session: AsyncSession = Depends(getSession)
):
    """Delete a school"""
    result = await session.execute(select(School).where(School.uuid == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )

    # Clear director reference
    if school.director:
        school.director.managed_school_uuid = None
        await session.commit()

    await session.delete(school)
    await session.commit()