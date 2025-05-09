from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from .user import Roles


class InvitationType(str, Enum):
    CLASS_STUDENT = "class_student"  # Student joining a class
    CLASS_TEACHER = "class_teacher"  # Teacher joining a class
    SUBJECT_TEACHER = "subject_teacher"  # Teacher joining a specific subject
    PARENT_CHILD = "parent_child"  # Parent connecting to their child
    CLASS_PARENT = "class_parent"  # Parent joining a class to monitor their child


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class InvitationBase(BaseModel):
    type: InvitationType
    role: Roles
    class_uuid: Optional[UUID] = None
    subject_uuid: Optional[UUID] = None
    child_uuid: Optional[UUID] = None  # For parent invitations
    inviter_uuid: UUID
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + datetime.timedelta(days=7))


class InvitationCreate(InvitationBase):
    pass


class InvitationUpdate(BaseModel):
    status: InvitationStatus


class Invitation(InvitationBase):
    uuid: UUID
    status: InvitationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvitationResponse(BaseModel):
    """Response model for invitation creation/acceptance"""
    invitation_uuid: UUID
    invite_link: str
    role: Roles
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    child_name: Optional[str] = None
    expires_at: datetime 