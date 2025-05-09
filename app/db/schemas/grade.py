from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class GradeBase(BaseModel):
    student_id: int
    subject_id: int
    value: float = Field(..., ge=1.0, le=5.0)  # Grade must be between 1 and 5
    date: datetime
    comment: Optional[str] = None

class GradeCreate(GradeBase):
    pass

class GradeUpdate(BaseModel):
    student_id: Optional[int] = None
    subject_id: Optional[int] = None
    value: Optional[float] = Field(None, ge=1.0, le=5.0)
    date: Optional[datetime] = None
    comment: Optional[str] = None

class GradeResponse(GradeBase):
    id: int
    uuid: UUID

    class Config:
        from_attributes = True 