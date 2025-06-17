from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class GradeBase(BaseModel):
    value: float
    subject_uuid: UUID


class GradeCreate(GradeBase):
    user_uuid: UUID


class GradeUpdate(BaseModel):
    value: Optional[float] = None
    subject_uuid: Optional[UUID] = None
    user_uuid: Optional[UUID] = None


class GradeInDB(GradeBase):
    uuid: UUID
    user_uuid: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GradeResponse(GradeInDB):
    subject_name: str
    user_name: str

    class Config:
        from_attributes = True


class Grade(GradeInDB):
    pass
