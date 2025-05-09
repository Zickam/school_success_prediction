from enum import Enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from app.utility import AutoNameEnum, auto


class Roles(str, AutoNameEnum):
    student = auto()  # Ученик
    homeroom_teacher = auto()  # Классный руководитель
    subject_teacher = auto()  # Учитель-предметник
    deputy_principal = auto()  # Завуч
    principal = auto()  # Директор
    parent = auto()  # Родитель


class TeacherSubject(BaseModel):
    subject_uuid: UUID
    subject_name: str


class ParentChild(BaseModel):
    child_uuid: UUID
    child_name: str


# For reading
class UserRead(BaseModel):
    uuid: UUID
    role: Roles
    name: str | None
    chat_id: int | None
    teacher_subjects: List[TeacherSubject] | None = None
    parent_children: List[ParentChild] | None = None

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    name: str
    role: Roles
    chat_id: int
    teacher_subjects: List[TeacherSubject] | None = None
    parent_children: List[ParentChild] | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Roles] = None
    chat_id: Optional[int] = None
    teacher_subjects: Optional[List[TeacherSubject]] = None
    parent_children: Optional[List[ParentChild]] = None


class UserInDB(UserBase):
    uuid: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserInDB):
    pass
