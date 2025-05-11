from datetime import datetime
from typing import List
from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum, Table, Column, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
from app.db.schemas.user import Roles
import enum
import uuid

# Association tables
teacher_subject = Table(
    "teacher_subject",
    Base.metadata,
    Column("teacher_uuid", UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=True),
    Column("subject_uuid", UUID(as_uuid=True), ForeignKey("subject.uuid"), primary_key=True)
)

parent_child = Table(
    "parent_child",
    Base.metadata,
    Column("parent_uuid", UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=True),
    Column("child_uuid", UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=True)
)

user_class = Table(
    "user_class",
    Base.metadata,
    Column("user_uuid", UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=True),
    Column("class_uuid", UUID(as_uuid=True), ForeignKey("class.uuid"), primary_key=True)
)

class User(Base):
    """User model for authentication"""
    __tablename__ = "user"

    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[Roles] = mapped_column(Enum(Roles))
    managed_class_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("class.uuid"), nullable=True)
    school_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("school.uuid"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    classes: Mapped[List["Class"]] = relationship(secondary=user_class, back_populates="users")
    grades: Mapped[List["Grade"]] = relationship(back_populates="user")
    managed_class: Mapped["Class"] = relationship(back_populates="homeroom_teacher", foreign_keys=[managed_class_uuid])
    school: Mapped["School"] = relationship(back_populates="teachers")
    subjects: Mapped[List["Subject"]] = relationship(secondary=teacher_subject, back_populates="teachers")
    children: Mapped[List["User"]] = relationship(
        "User",
        secondary=parent_child,
        primaryjoin="User.uuid==parent_child.c.parent_uuid",
        secondaryjoin="User.uuid==parent_child.c.child_uuid",
        backref="parents"
    )
    attendance: Mapped[List["Attendance"]] = relationship(back_populates="user")

class School(Base):
    """School model"""
    __tablename__ = "school"

    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    classes: Mapped[List["Class"]] = relationship(back_populates="school")
    subjects: Mapped[List["Subject"]] = relationship(back_populates="school")
    teachers: Mapped[List["User"]] = relationship(
        "User",
        primaryjoin="and_(School.uuid==User.school_uuid, User.role.in_(['homeroom_teacher', 'subject_teacher']))",
        back_populates="school"
    )

class Subject(Base):
    """Subject model"""
    __tablename__ = "subject"

    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    school_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("school.uuid"))
    class_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("class.uuid"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school: Mapped["School"] = relationship(back_populates="subjects")
    class_: Mapped["Class"] = relationship(back_populates="subjects")
    teachers: Mapped[List["User"]] = relationship(secondary=teacher_subject, back_populates="subjects")
    grades: Mapped[List["Grade"]] = relationship(back_populates="subject")

class Class(Base):
    """Class model"""
    __tablename__ = "class"

    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50))
    start_year: Mapped[int] = mapped_column(Integer)
    school_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("school.uuid"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school: Mapped["School"] = relationship(back_populates="classes")
    homeroom_teacher: Mapped["User"] = relationship(back_populates="managed_class", foreign_keys="[User.managed_class_uuid]")
    users: Mapped[List["User"]] = relationship(secondary=user_class, back_populates="classes")
    subjects: Mapped[List["Subject"]] = relationship(back_populates="class_")

class Grade(Base):
    """Grade model"""
    __tablename__ = "grade"

    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("user.uuid"))
    subject_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("subject.uuid"))
    value: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="grades")
    subject: Mapped["Subject"] = relationship(back_populates="grades")

class AttendanceStatus(enum.Enum):
    """Attendance status enum"""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"

class Attendance(Base):
    """Attendance model"""
    __tablename__ = "attendance"

    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("user.uuid"))
    date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(Enum(AttendanceStatus))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="attendance") 