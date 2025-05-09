from enum import Enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.utility import AutoNameEnum, auto


class Roles(str, Enum):
    student = "student"
    parent = "parent"
    subject_teacher = "subject_teacher"
    homeroom_teacher = "homeroom_teacher"
    deputy_principal = "deputy_principal"
    principal = "principal"

    @classmethod
    def get_hierarchy_level(cls, role: "Roles") -> int:
        """Returns the hierarchy level of a role (higher number = more permissions)"""
        hierarchy = {
            cls.student: 0,
            cls.parent: 1,
            cls.subject_teacher: 2,
            cls.homeroom_teacher: 3,
            cls.deputy_principal: 4,
            cls.principal: 5
        }
        return hierarchy[role]

    def can_manage(self, other_role: "Roles") -> bool:
        """Checks if this role can manage the other role"""
        return self.get_hierarchy_level(self) > self.get_hierarchy_level(other_role)

    def can_invite(self, target_role: "Roles") -> bool:
        """Checks if this role can invite users with the target role"""
        # Special case: parents can only invite other parents
        if self == Roles.parent:
            return target_role == Roles.parent
        
        # Special case: subject teachers can only invite students
        if self == Roles.subject_teacher:
            return target_role == Roles.student
        
        # For other roles, use hierarchy
        return self.get_hierarchy_level(self) > self.get_hierarchy_level(target_role)


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


class User(UserInDB):
    pass
