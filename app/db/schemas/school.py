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
