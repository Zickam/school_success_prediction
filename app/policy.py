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

        if viewer.uuid == target.uuid:
            return True

        if viewer.role == Roles.parent and target.uuid in (
            viewer.parent_children or []
        ):
            return True

        if viewer.role in [Roles.subject_teacher, Roles.homeroom_teacher]:
            viewer_classes = set(c.uuid for c in viewer.classes)
            target_classes = set(c.uuid for c in target.classes)
            if viewer_classes.intersection(target_classes):
                return True

        if viewer.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False

    async def can_manage_user(self, manager: User, target: User) -> bool:

        return manager.role.can_manage(target.role)

    async def can_view_grade(self, viewer: User, grade: Grade) -> bool:

        result = await self.session.execute(
            select(User, Subject)
            .join(Grade, Grade.user_uuid == User.uuid)
            .join(Subject, Grade.subject_uuid == Subject.uuid)
            .where(Grade.uuid == grade.uuid)
        )
        owner, subject = result.first()

        if viewer.uuid == owner.uuid:
            return True

        if viewer.role == Roles.parent and owner.uuid in (viewer.parent_children or []):
            return True

        if viewer.role == Roles.subject_teacher:
            if subject.uuid in (viewer.teacher_subjects or []):
                return True

        if viewer.role == Roles.homeroom_teacher:
            owner_classes = set(c.uuid for c in owner.classes)
            teacher_classes = set(c.uuid for c in viewer.classes)
            if owner_classes.intersection(teacher_classes):
                return True

        if viewer.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False

    async def can_manage_grade(self, manager: User, grade: Grade) -> bool:

        result = await self.session.execute(
            select(Subject).where(Subject.uuid == grade.subject_uuid)
        )
        subject = result.scalar_one()

        if manager.role == Roles.subject_teacher:
            return subject.uuid in (manager.teacher_subjects or [])

        if manager.role == Roles.homeroom_teacher:
            result = await self.session.execute(
                select(User)
                .join(Grade, Grade.user_uuid == User.uuid)
                .where(Grade.uuid == grade.uuid)
            )
            student = result.scalar_one()
            student_classes = set(c.uuid for c in student.classes)
            teacher_classes = set(c.uuid for c in manager.classes)
            return bool(student_classes.intersection(teacher_classes))

        if manager.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False

    async def can_view_grades(self, viewer: User, student: User) -> bool:

        if viewer.role == Roles.student:
            return viewer.uuid == student.uuid

        if viewer.role == Roles.parent:
            return student.uuid in (viewer.parent_children or [])

        if viewer.role in [Roles.subject_teacher, Roles.homeroom_teacher]:
            student_classes = [c.uuid for c in student.classes]
            teacher_classes = [c.uuid for c in viewer.classes]
            return any(c in teacher_classes for c in student_classes)

        if viewer.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False

    async def can_edit_grades(
        self, editor: User, student: User, subject: Subject
    ) -> bool:

        if editor.role not in [
            Roles.subject_teacher,
            Roles.homeroom_teacher,
            Roles.deputy_principal,
            Roles.principal,
        ]:
            return False

        if editor.role == Roles.subject_teacher:
            return subject.uuid in (editor.teacher_subjects or [])

        if editor.role == Roles.homeroom_teacher:
            return any(c.uuid == editor.managed_class.uuid for c in student.classes)

        if editor.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False
