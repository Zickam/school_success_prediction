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
        return manager.role.can_manage(target.role)

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

    async def can_view_grades(self, viewer: User, student: User) -> bool:
        """Check if viewer can view student's grades"""
        # Students can only view their own grades
        if viewer.role == Roles.student:
            return viewer.uuid == student.uuid

        # Parents can view their children's grades
        if viewer.role == Roles.parent:
            return student.uuid in (viewer.parent_children or [])

        # Teachers can view grades of students in their classes
        if viewer.role in [Roles.subject_teacher, Roles.homeroom_teacher]:
            # Get student's classes
            student_classes = [c.uuid for c in student.classes]
            # Get teacher's classes
            teacher_classes = [c.uuid for c in viewer.classes]
            return any(c in teacher_classes for c in student_classes)

        # Admins can view all grades
        if viewer.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False

    async def can_edit_grades(self, editor: User, student: User, subject: Subject) -> bool:
        """Check if editor can edit grades for a student in a subject"""
        # Only teachers and admins can edit grades
        if editor.role not in [Roles.subject_teacher, Roles.homeroom_teacher, 
                             Roles.deputy_principal, Roles.principal]:
            return False

        # Subject teachers can only edit grades for their subjects
        if editor.role == Roles.subject_teacher:
            return subject.uuid in (editor.teacher_subjects or [])

        # Homeroom teachers can edit grades for students in their class
        if editor.role == Roles.homeroom_teacher:
            return any(c.uuid == editor.managed_class.uuid for c in student.classes)

        # Admins can edit all grades
        if editor.role in [Roles.deputy_principal, Roles.principal]:
            return True

        return False 