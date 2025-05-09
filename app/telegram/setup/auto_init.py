import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.declaration import User, School, Class, Subject
from app.db.schemas.user import Roles

class AutoInitializer:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.is_enabled = os.getenv("ENABLE_AUTO_SETUP", "").lower() == "true"

    async def initialize(self) -> None:
        """Initialize demo data if enabled"""
        if not self.is_enabled:
            return

        # Check if data already exists
        if await self._check_data_exists():
            return

        # Create demo data
        await self._create_demo_school()
        await self._create_demo_subjects()
        await self._create_demo_teachers()
        await self._create_demo_class()

    async def _check_data_exists(self) -> bool:
        """Check if demo data already exists"""
        # Check for any school
        result = await self.session.execute(select(School))
        return result.scalar_one_or_none() is not None

    async def _create_demo_school(self) -> None:
        """Create a demo school"""
        school = School(
            facility_name="Demo School",
            address="123 Education St."
        )
        self.session.add(school)
        await self.session.commit()
        await self.session.refresh(school)
        return school

    async def _create_demo_subjects(self) -> list[Subject]:
        """Create demo subjects"""
        subjects = [
            Subject(name="Mathematics"),
            Subject(name="Literature"),
            Subject(name="Physics"),
            Subject(name="History"),
            Subject(name="English")
        ]
        for subject in subjects:
            self.session.add(subject)
        await self.session.commit()
        for subject in subjects:
            await self.session.refresh(subject)
        return subjects

    async def _create_demo_teachers(self) -> list[User]:
        """Create demo teacher accounts"""
        teachers = [
            User(
                name="Ivan Petrov",
                role=Roles.homeroom_teacher,
                chat_id=1001,  # Demo chat IDs
                teacher_subjects=["Mathematics"]
            ),
            User(
                name="Maria Ivanova",
                role=Roles.subject_teacher,
                chat_id=1002,
                teacher_subjects=["Literature", "English"]
            ),
            User(
                name="Alexey Smirnov",
                role=Roles.subject_teacher,
                chat_id=1003,
                teacher_subjects=["Physics"]
            ),
            User(
                name="Elena Kuznetsova",
                role=Roles.subject_teacher,
                chat_id=1004,
                teacher_subjects=["History"]
            )
        ]
        for teacher in teachers:
            self.session.add(teacher)
        await self.session.commit()
        for teacher in teachers:
            await self.session.refresh(teacher)
        return teachers

    async def _create_demo_class(self) -> None:
        """Create a demo class with students"""
        # Create class
        class_ = Class(
            class_name="9-A",
            start_year=2024,  # Added required start_year field
            homeroom_teacher_uuid=None  # Will be set after teacher creation
        )
        self.session.add(class_)
        await self.session.commit()
        await self.session.refresh(class_)

        # Get homeroom teacher
        result = await self.session.execute(
            select(User).where(User.role == Roles.homeroom_teacher)
        )
        homeroom_teacher = result.scalar_one()
        class_.homeroom_teacher_uuid = homeroom_teacher.uuid

        # Create demo students
        students = [
            User(
                name="Student One",
                role=Roles.student,
                chat_id=2001,
                classes=[class_]
            ),
            User(
                name="Student Two",
                role=Roles.student,
                chat_id=2002,
                classes=[class_]
            ),
            User(
                name="Student Three",
                role=Roles.student,
                chat_id=2003,
                classes=[class_]
            )
        ]
        for student in students:
            self.session.add(student)

        # Create demo parent
        parent = User(
            name="Parent One",
            role=Roles.parent,
            chat_id=3001,
            parent_children=[students[0].uuid, students[1].uuid]
        )
        self.session.add(parent)

        await self.session.commit() 