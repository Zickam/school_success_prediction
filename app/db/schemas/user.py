from pydantic import BaseModel
from uuid import UUID

from app.utility import AutoNameEnum, auto


class Roles(str, AutoNameEnum):
    student: str = auto()
    teacher: str = auto()
    principal: str = auto()
    admin: str = auto()


# For reading
class UserRead(BaseModel):
    uuid: UUID
    role: Roles
    name: str | None
    chat_id: int | None

    class Config:
        from_attributes = True  # 👈 Required to work with ORM objects

# For creating
class UserCreate(BaseModel):
    name: str | None = None
    role: Roles
    chat_id: int | None = None
