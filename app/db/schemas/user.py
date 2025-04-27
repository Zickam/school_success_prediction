from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.utility import AutoNameEnum, auto


class Roles(str, AutoNameEnum):
    admin = auto()
    teacher = auto()
    student = auto()
    parent = auto()


# For reading
class UserRead(BaseModel):
    uuid: UUID
    role: Roles
    name: str | None
    chat_id: int | None

    class Config:
        from_attributes = True  # 👈 Required to work with ORM objects


class UserBase(BaseModel):
    name: str
    role: Roles
    chat_id: int


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Roles] = None
    chat_id: Optional[int] = None


class UserInDB(UserBase):
    uuid: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserInDB):
    pass
