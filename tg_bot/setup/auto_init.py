import os
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import School, Subject, User, Class
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

            # Create demo class first
            class_ = await self._create_demo_class(school)
            if not class_:
                logger.error("Failed to create demo class")
                return

            # Create demo subjects
            subjects = await self._create_demo_subjects(school, class_)
            if not subjects:
                logger.error("Failed to create demo subjects")
                return

            # Create demo teachers
            teachers = await self._create_demo_teachers(school, subjects)
            if not teachers:
                logger.error("Failed to create demo teachers")
                return

            # Set homeroom teacher for the class
            teachers[0].managed_class_uuid = class_.uuid
            await self.session.commit()
            await self.session.refresh(teachers[0])

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

    async def _create_demo_class(self, school: School) -> Optional[Class]:
        """Create demo class"""
        try:
            class_ = Class(
                name="9A",
                school_uuid=school.uuid,
                start_year=2024
            )
            self.session.add(class_)
            await self.session.commit()
            await self.session.refresh(class_)
            return class_
        except Exception as e:
            logger.error(f"Error creating demo class: {e}")
            await self.session.rollback()
            return None

    async def _create_demo_subjects(self, school: School, class_: Class) -> Optional[list[Subject]]:
        """Create demo subjects"""
        try:
            subjects = [
                Subject(name="Mathematics", school_uuid=school.uuid, class_uuid=class_.uuid),
                Subject(name="Physics", school_uuid=school.uuid, class_uuid=class_.uuid),
                Subject(name="Chemistry", school_uuid=school.uuid, class_uuid=class_.uuid),
                Subject(name="Biology", school_uuid=school.uuid, class_uuid=class_.uuid),
                Subject(name="English", school_uuid=school.uuid, class_uuid=class_.uuid)
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

    async def _create_demo_teachers(self, school: School, subjects: list[Subject]) -> Optional[list[User]]:
        """Create demo teachers"""
        try:
            teachers = [
                User(
                    name="John Doe",
                    role=Roles.homeroom_teacher,
                    school_uuid=school.uuid,
                    subjects=[subjects[0], subjects[1]]  # Math and Physics
                ),
                User(
                    name="Jane Smith",
                    role=Roles.subject_teacher,
                    school_uuid=school.uuid,
                    subjects=[subjects[2], subjects[3]]  # Chemistry and Biology
                ),
                User(
                    name="Bob Johnson",
                    role=Roles.subject_teacher,
                    school_uuid=school.uuid,
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