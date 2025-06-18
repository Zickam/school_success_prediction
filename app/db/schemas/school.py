import datetime

from pydantic import BaseModel
from uuid import UUID


class SchoolRead(BaseModel):
    uuid: UUID | None = None
    facility_name: str | None = None

    class Config:
        from_attributes = True  # 👈 Required to work with ORM objects


class SchoolCreate(BaseModel):
    facility_name: str


class ClassRead(BaseModel):
    uuid: UUID
    start_year: int
    class_name: str
    school_uuid: UUID

    class Config:
        from_attributes = True


class ClassCreate(BaseModel):
    start_year: int
    class_name: str
    school_uuid: UUID


class UserClassMarkRead(BaseModel):
    uuid: UUID
    user_uuid: UUID
    class_uuid: UUID
    mark: float
    discipline: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class UserClassMarkCreate(BaseModel):
    user_uuid: UUID
    class_uuid: UUID
    mark: float
    discipline: str
    created_at: datetime.datetime | None = None