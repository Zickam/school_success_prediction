import os
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import School, Subject, Teacher, Class
from app.db.schemas.user import Roles

logger = logging.getLogger(__name__)

class AutoInitializer:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def initialize(self) -> None:
        """Initialize demo data if enabled"""
        if not os.getenv("ENABLE_AUTO_SETUP", "false").lower() == "true":
            logger.info("Auto-initialization is disabled")
            return

        logger.info("Starting auto-initialization")
        try:
            # Create demo school
            school = await self._create_demo_school()
            if not school:
                logger.error("Failed to create demo school")
                return

            # Create demo subjects
            subjects = await self._create_demo_subjects(school)
            if not subjects:
                logger.error("Failed to create demo subjects")
                return

            # Create demo teachers
            teachers = await self._create_demo_teachers(school, subjects)
            if not teachers:
                logger.error("Failed to create demo teachers")
                return

            # Create demo class
            class_ = await self._create_demo_class(school, teachers)
            if not class_:
                logger.error("Failed to create demo class")
                return

            logger.info("Auto-initialization completed successfully")
        except Exception as e:
            logger.error(f"Error during auto-initialization: {e}")
            raise

    async def _create_demo_school(self) -> Optional[School]:
        """Create demo school"""
        try:
            school = School(
                name="Demo School",
                address="123 Demo Street",
                phone="+1234567890",
                email="demo@school.com"
            )
            self.session.add(school)
            await self.session.commit()
            await self.session.refresh(school)
            return school
        except Exception as e:
            logger.error(f"Error creating demo school: {e}")
            await self.session.rollback()
            return None

    async def _create_demo_subjects(self, school: School) -> Optional[list[Subject]]:
        """Create demo subjects"""
        try:
            subjects = [
                Subject(name="Mathematics", school_id=school.id),
                Subject(name="Physics", school_id=school.id),
                Subject(name="Chemistry", school_id=school.id),
                Subject(name="Biology", school_id=school.id),
                Subject(name="English", school_id=school.id)
            ]
            for subject in subjects:
                self.session.add(subject)
            await self.session.commit()
            for subject in subjects:
                await self.session.refresh(subject)
            return subjects
        except Exception as e:
            logger.error(f"Error creating demo subjects: {e}")
            await self.session.rollback()
            return None

    async def _create_demo_teachers(self, school: School, subjects: list[Subject]) -> Optional[list[Teacher]]:
        """Create demo teachers"""
        try:
            teachers = [
                Teacher(
                    name="John Doe",
                    role=Roles.homeroom_teacher,
                    school_id=school.id,
                    subjects=[subjects[0], subjects[1]]  # Math and Physics
                ),
                Teacher(
                    name="Jane Smith",
                    role=Roles.subject_teacher,
                    school_id=school.id,
                    subjects=[subjects[2], subjects[3]]  # Chemistry and Biology
                ),
                Teacher(
                    name="Bob Johnson",
                    role=Roles.subject_teacher,
                    school_id=school.id,
                    subjects=[subjects[4]]  # English
                )
            ]
            for teacher in teachers:
                self.session.add(teacher)
            await self.session.commit()
            for teacher in teachers:
                await self.session.refresh(teacher)
            return teachers
        except Exception as e:
            logger.error(f"Error creating demo teachers: {e}")
            await self.session.rollback()
            return None

    async def _create_demo_class(self, school: School, teachers: list[Teacher]) -> Optional[Class]:
        """Create demo class"""
        try:
            class_ = Class(
                name="9A",
                school_id=school.id,
                homeroom_teacher_id=teachers[0].id
            )
            self.session.add(class_)
            await self.session.commit()
            await self.session.refresh(class_)
            return class_
        except Exception as e:
            logger.error(f"Error creating demo class: {e}")
            await self.session.rollback()
            return None 