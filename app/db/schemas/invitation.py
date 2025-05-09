from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from .user import Roles


class InvitationType(str, Enum):
    class_invite = "class_invite"  # Invite to join a class
    subject_invite = "subject_invite"  # Invite to join a subject
    parent_invite = "parent_invite"  # Invite to link as parent
    teacher_invite = "teacher_invite"  # Invite to join as teacher


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class InvitationBase(BaseModel):
    type: InvitationType
    role: Roles
    class_uuid: Optional[UUID] = None  # Required for class_invite
    subject_uuid: Optional[UUID] = None  # Required for subject_invite
    child_uuid: Optional[UUID] = None  # Required for parent_invite
    expires_at: datetime


class InvitationCreate(InvitationBase):
    inviter_uuid: UUID


class InvitationUpdate(BaseModel):
    status: InvitationStatus


class Invitation(InvitationBase):
    uuid: UUID
    inviter_uuid: UUID
    status: InvitationStatus = InvitationStatus.PENDING
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvitationResponse(Invitation):
    invite_link: str 