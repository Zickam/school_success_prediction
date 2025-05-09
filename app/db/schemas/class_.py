from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ClassBase(BaseModel):
    class_name: str
    homeroom_teacher_uuid: Optional[UUID] = None

class ClassCreate(ClassBase):
    pass

class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    homeroom_teacher_uuid: Optional[UUID] = None

class ClassResponse(ClassBase):
    id: int
    uuid: UUID

    class Config:
        from_attributes = True 