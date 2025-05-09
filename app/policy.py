from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .db.declaration import User, Class, Subject, Grade
from .db.schemas.user import Roles

class PolicyManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def can_view_user(self, viewer: User, target: User) -> bool:
        """Check if viewer can view target user's data"""
        # Users can always view their own data
        if viewer.uuid == target.uuid:
            return True

        # Parents can view their children's data
        if viewer.role == Roles.parent and target.uuid in (viewer.parent_children or []):
            return True

        # Teachers can view their students' data
        if viewer.role in [Roles.subject_teacher, Roles.homeroom_teacher]:
            # Get shared classes
            viewer_classes = set(c.uuid for c in viewer.classes)
            target_classes = set(c.uuid for c in target.classes)
            if viewer_classes.intersection(target_classes):
                return True

        # Admins can view all users
        if viewer.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False

    async def can_manage_user(self, manager: User, target: User) -> bool:
        """Check if manager can manage target user"""
        # Users can't manage themselves
        if manager.uuid == target.uuid:
            return False

        # Check role hierarchy
        if not manager.role.can_manage(target.role):
            return False

        # Additional checks for specific roles
        if manager.role == Roles.subject_teacher:
            # Subject teachers can only manage students in their subjects
            shared_classes = set(c.uuid for c in manager.classes).intersection(
                set(c.uuid for c in target.classes)
            )
            return bool(shared_classes)

        return True

    async def can_view_grade(self, viewer: User, grade: Grade) -> bool:
        """Check if viewer can view a grade"""
        # Get the grade's owner and subject
        result = await self.session.execute(
            select(User, Subject).join(
                Grade, Grade.user_uuid == User.uuid
            ).join(
                Subject, Grade.subject_uuid == Subject.uuid
            ).where(Grade.uuid == grade.uuid)
        )
        owner, subject = result.first()

        # Users can view their own grades
        if viewer.uuid == owner.uuid:
            return True

        # Parents can view their children's grades
        if viewer.role == Roles.parent and owner.uuid in (viewer.parent_children or []):
            return True

        # Subject teachers can view grades for their subjects
        if viewer.role == Roles.subject_teacher:
            if subject.uuid in (viewer.teacher_subjects or []):
                return True

        # Homeroom teachers can view grades for their class
        if viewer.role == Roles.homeroom_teacher:
            owner_classes = set(c.uuid for c in owner.classes)
            teacher_classes = set(c.uuid for c in viewer.classes)
            if owner_classes.intersection(teacher_classes):
                return True

        # Admins can view all grades
        if viewer.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False

    async def can_manage_grade(self, manager: User, grade: Grade) -> bool:
        """Check if manager can manage a grade"""
        # Get the grade's subject
        result = await self.session.execute(
            select(Subject).where(Subject.uuid == grade.subject_uuid)
        )
        subject = result.scalar_one()

        # Subject teachers can manage grades for their subjects
        if manager.role == Roles.subject_teacher:
            return subject.uuid in (manager.teacher_subjects or [])

        # Homeroom teachers can manage grades for their class
        if manager.role == Roles.homeroom_teacher:
            result = await self.session.execute(
                select(User).join(
                    Grade, Grade.user_uuid == User.uuid
                ).where(Grade.uuid == grade.uuid)
            )
            student = result.scalar_one()
            student_classes = set(c.uuid for c in student.classes)
            teacher_classes = set(c.uuid for c in manager.classes)
            return bool(student_classes.intersection(teacher_classes))

        # Admins can manage all grades
        if manager.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False

    async def can_invite_to_class(self, inviter: User, class_: Class, target_role: Roles) -> bool:
        """Check if inviter can invite someone to a class"""
        # Check if inviter has permission to invite for this role
        if not inviter.role.can_invite(target_role):
            return False

        # Check if inviter has access to the class
        if inviter.role == Roles.subject_teacher:
            # Subject teachers can only invite students to classes they teach
            return class_.uuid in (c.uuid for c in inviter.classes)

        if inviter.role == Roles.homeroom_teacher:
            # Homeroom teachers can invite students to their class
            return class_.uuid in (c.uuid for c in inviter.classes)

        # Admins can invite to any class
        if inviter.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False

    async def can_invite_to_subject(self, inviter: User, subject: Subject, target_role: Roles) -> bool:
        """Check if inviter can invite someone to a subject"""
        # Check if inviter has permission to invite for this role
        if not inviter.role.can_invite(target_role):
            return False

        # Subject teachers can invite students to their subjects
        if inviter.role == Roles.subject_teacher:
            return subject.uuid in (inviter.teacher_subjects or [])

        # Admins can invite to any subject
        if inviter.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False 