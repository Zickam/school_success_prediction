from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class SchoolBase(BaseModel):
    facility_name: str
    address: str


class SchoolCreate(SchoolBase):
    pass


class SchoolUpdate(BaseModel):
    facility_name: Optional[str] = None
    address: Optional[str] = None


class SchoolInDB(SchoolBase):
    uuid: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class School(SchoolInDB):
    pass


class ClassBase(BaseModel):
    start_year: int
    class_name: str
    school_uuid: UUID


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    start_year: Optional[int] = None
    class_name: Optional[str] = None
    school_uuid: Optional[UUID] = None


class ClassInDB(ClassBase):
    uuid: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Class(ClassInDB):
    pass


class SubjectBase(BaseModel):
    name: str
    class_uuid: UUID


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    class_uuid: Optional[UUID] = None


class SubjectInDB(SubjectBase):
    uuid: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Subject(SubjectInDB):
    pass


class GradeBase(BaseModel):
    value: float
    user_uuid: UUID
    subject_uuid: UUID


class GradeCreate(GradeBase):
    pass


class GradeUpdate(BaseModel):
    value: Optional[float] = None
    user_uuid: Optional[UUID] = None
    subject_uuid: Optional[UUID] = None


class GradeInDB(GradeBase):
    uuid: UUID
    date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Grade(GradeInDB):
    pass
