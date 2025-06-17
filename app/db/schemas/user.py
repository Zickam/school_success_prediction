from enum import Enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.utility import AutoNameEnum, auto


class Roles(str, Enum):

    principal = "principal"
    deputy_principal = "deputy_principal"
    homeroom_teacher = "homeroom_teacher"
    subject_teacher = "subject_teacher"
    parent = "parent"
    student = "student"

    @classmethod
    def get_hierarchy_level(cls, role: "Roles") -> int:

        hierarchy = {
            cls.student: 0,
            cls.parent: 1,
            cls.subject_teacher: 2,
            cls.homeroom_teacher: 3,
            cls.deputy_principal: 4,
            cls.principal: 5,
        }
        return hierarchy[role]

    def can_manage(self, other_role: "Roles") -> bool:

        return self.get_hierarchy_level(self) > self.get_hierarchy_level(other_role)


class TeacherSubject(BaseModel):
    subject_uuid: UUID
    subject_name: str


class ParentChild(BaseModel):
    child_uuid: UUID
    child_name: str


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
    chat_id: int
    name: str
    role: Roles
    teacher_subjects: List[TeacherSubject] | None = None
    parent_children: List[ParentChild] | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Roles] = None
    chat_id: Optional[int] = None
    teacher_subjects: Optional[List[UUID]] = None
    parent_children: Optional[List[UUID]] = None


class UserInDB(UserBase):
    uuid: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    pass


User = UserResponse
