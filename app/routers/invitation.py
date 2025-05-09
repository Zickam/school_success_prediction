from __future__ import annotations
import os
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db.engine import getSession
from ..db.declaration import User, Class, Subject, Invitation
from ..db.schemas.invitation import (
    InvitationCreate, InvitationUpdate, Invitation as InvitationSchema,
    InvitationResponse, InvitationType, InvitationStatus
)
from ..policy import PolicyManager

router = APIRouter(tags=["Invitation"], prefix="/invitations")

@router.post("/", response_model=InvitationResponse)
async def create_invitation(
    invitation: InvitationCreate,
    session: AsyncSession = Depends(getSession)
):
    # Get inviter
    result = await session.execute(
        select(User).where(User.uuid == invitation.inviter_uuid)
    )
    inviter = result.scalar_one_or_none()
    if not inviter:
        raise HTTPException(status_code=404, detail="Inviter not found")

    # Initialize policy manager
    policy = PolicyManager(session)

    # Validate invitation based on type
    if invitation.type == InvitationType.class_invite:
        if not invitation.class_uuid:
            raise HTTPException(status_code=400, detail="Class UUID required for class invitation")
        
        result = await session.execute(
            select(Class).where(Class.uuid == invitation.class_uuid)
        )
        class_ = result.scalar_one_or_none()
        if not class_:
            raise HTTPException(status_code=404, detail="Class not found")

        if not await policy.can_invite_to_class(inviter, class_, invitation.role):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to invite to this class"
            )

    elif invitation.type == InvitationType.subject_invite:
        if not invitation.subject_uuid:
            raise HTTPException(status_code=400, detail="Subject UUID required for subject invitation")
        
        result = await session.execute(
            select(Subject).where(Subject.uuid == invitation.subject_uuid)
        )
        subject = result.scalar_one_or_none()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        if not await policy.can_invite_to_subject(inviter, subject, invitation.role):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to invite to this subject"
            )

    elif invitation.type == InvitationType.parent_invite:
        if not invitation.child_uuid:
            raise HTTPException(status_code=400, detail="Child UUID required for parent invitation")
        
        result = await session.execute(
            select(User).where(User.uuid == invitation.child_uuid)
        )
        child = result.scalar_one_or_none()
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")

        # Only parents can invite other parents
        if inviter.role != "parent":
            raise HTTPException(
                status_code=403,
                detail="Only parents can invite other parents"
            )

    # Create invitation
    db_invitation = Invitation(**invitation.model_dump())
    session.add(db_invitation)
    await session.commit()
    await session.refresh(db_invitation)

    # Generate invite link
    invite_link = f"t.me/{os.getenv('BOT_URL')}?start=invite_{db_invitation.uuid}"

    return InvitationResponse(**db_invitation.model_dump(), invite_link=invite_link)

@router.get("/{invitation_uuid}", response_model=InvitationSchema)
async def get_invitation(
    invitation_uuid: UUID,
    session: AsyncSession = Depends(getSession)
):
    result = await session.execute(
        select(Invitation).where(Invitation.uuid == invitation_uuid)
    )
    invitation = result.scalar_one_or_none()
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
    result = await session.execute(
        select(Invitation).where(Invitation.uuid == invitation_uuid)
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # Check if invitation is still valid
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invitation is no longer valid")
    if invitation.expires_at < datetime.utcnow():
        invitation.status = InvitationStatus.EXPIRED
        await session.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired")

    # Get user
    result = await session.execute(
        select(User).where(User.uuid == user_uuid)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Process invitation based on type
    if invitation.type == InvitationType.class_invite:
        if not invitation.class_uuid:
            raise HTTPException(status_code=400, detail="Class UUID required for class invitation")
        
        result = await session.execute(
            select(Class).where(Class.uuid == invitation.class_uuid)
        )
        class_ = result.scalar_one_or_none()
        if not class_:
            raise HTTPException(status_code=404, detail="Class not found")

        # Add user to class
        user.classes.append(class_)

    elif invitation.type == InvitationType.subject_invite:
        if not invitation.subject_uuid:
            raise HTTPException(status_code=400, detail="Subject UUID required for subject invitation")
        
        result = await session.execute(
            select(Subject).where(Subject.uuid == invitation.subject_uuid)
        )
        subject = result.scalar_one_or_none()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        # Add subject to user's subjects
        if not user.teacher_subjects:
            user.teacher_subjects = []
        user.teacher_subjects.append(subject.uuid)

    elif invitation.type == InvitationType.parent_invite:
        if not invitation.child_uuid:
            raise HTTPException(status_code=400, detail="Child UUID required for parent invitation")
        
        result = await session.execute(
            select(User).where(User.uuid == invitation.child_uuid)
        )
        child = result.scalar_one_or_none()
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")

        # Add child to parent's children
        if not user.parent_children:
            user.parent_children = []
        user.parent_children.append(child.uuid)

    # Update invitation status
    invitation.status = InvitationStatus.ACCEPTED
    await session.commit()
    await session.refresh(invitation)

    return invitation 