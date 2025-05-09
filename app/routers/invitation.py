from typing import List
from uuid import UUID
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ..db.engine import getSession
from ..db.declaration import User, Class, Subject, Invitation
from ..db.schemas.invitation import (
    InvitationCreate, InvitationUpdate, Invitation as InvitationSchema,
    InvitationResponse, InvitationType, InvitationStatus
)
from ..db.schemas.user import Roles

router = APIRouter(
    prefix="/invitations",
    tags=["invitations"]
)


@router.post("", response_model=InvitationResponse)
async def create_invitation(
    invitation: InvitationCreate,
    session: AsyncSession = Depends(getSession)
):
    # Validate inviter's permissions
    inviter = await session.get(User, invitation.inviter_uuid)
    if not inviter:
        raise HTTPException(status_code=404, detail="Inviter not found")

    # Check if inviter has permission to create this type of invitation
    if not await _can_create_invitation(inviter, invitation, session):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create this type of invitation"
        )

    # Create invitation
    db_invitation = Invitation(**invitation.model_dump())
    session.add(db_invitation)
    await session.commit()
    await session.refresh(db_invitation)

    # Generate invite link
    invite_link = f"t.me/{os.getenv('BOT_URL')}?start=invite|{db_invitation.uuid}"

    # Get additional context for response
    class_name = None
    subject_name = None
    child_name = None

    if db_invitation.class_uuid:
        class_ = await session.get(Class, db_invitation.class_uuid)
        if class_:
            class_name = class_.class_name

    if db_invitation.subject_uuid:
        subject = await session.get(Subject, db_invitation.subject_uuid)
        if subject:
            subject_name = subject.name

    if db_invitation.child_uuid:
        child = await session.get(User, db_invitation.child_uuid)
        if child:
            child_name = child.name

    return InvitationResponse(
        invitation_uuid=db_invitation.uuid,
        invite_link=invite_link,
        role=db_invitation.role,
        class_name=class_name,
        subject_name=subject_name,
        child_name=child_name,
        expires_at=db_invitation.expires_at
    )


@router.get("/{invitation_uuid}", response_model=InvitationSchema)
async def get_invitation(
    invitation_uuid: UUID,
    session: AsyncSession = Depends(getSession)
):
    invitation = await session.get(Invitation, invitation_uuid)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return invitation


@router.post("/{invitation_uuid}/accept", response_model=InvitationSchema)
async def accept_invitation(
    invitation_uuid: UUID,
    user_uuid: UUID,
    session: AsyncSession = Depends(getSession)
):
    # Get invitation
    invitation = await session.get(Invitation, invitation_uuid)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # Check if invitation is still valid
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invitation is no longer valid")

    # Get user
    user = await session.get(User, user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Process invitation based on type
    if invitation.type == InvitationType.CLASS_STUDENT:
        # Add student to class
        class_ = await session.get(Class, invitation.class_uuid)
        if class_:
            user.classes.append(class_)
    elif invitation.type == InvitationType.CLASS_TEACHER:
        # Add teacher to class
        class_ = await session.get(Class, invitation.class_uuid)
        if class_:
            user.classes.append(class_)
    elif invitation.type == InvitationType.SUBJECT_TEACHER:
        # Add teacher to subject
        if not user.teacher_subjects:
            user.teacher_subjects = []
        user.teacher_subjects.append(str(invitation.subject_uuid))
    elif invitation.type == InvitationType.PARENT_CHILD:
        # Connect parent to child
        if not user.parent_children:
            user.parent_children = []
        user.parent_children.append(str(invitation.child_uuid))

    # Update invitation status
    invitation.status = InvitationStatus.ACCEPTED
    await session.commit()
    await session.refresh(invitation)

    return invitation


async def _can_create_invitation(inviter: User, invitation: InvitationCreate, session: AsyncSession) -> bool:
    """Check if the inviter has permission to create this type of invitation"""
    if inviter.role == Roles.principal or inviter.role == Roles.deputy_principal:
        return True  # Principals can create any type of invitation

    if inviter.role == Roles.homeroom_teacher:
        # Homeroom teachers can invite students to their class and subject teachers
        if invitation.type in [InvitationType.CLASS_STUDENT, InvitationType.CLASS_TEACHER]:
            class_ = await session.get(Class, invitation.class_uuid)
            return class_ and class_.homeroom_teacher_uuid == inviter.uuid

    if inviter.role == Roles.subject_teacher:
        # Subject teachers can only invite students to their subject
        if invitation.type == InvitationType.SUBJECT_TEACHER:
            return str(invitation.subject_uuid) in (inviter.teacher_subjects or [])

    return False 