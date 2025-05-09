from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class SubjectResponse(SubjectBase):
    id: int
    uuid: UUID

    class Config:
        from_attributes = True 