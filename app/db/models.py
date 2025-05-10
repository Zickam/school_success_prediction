from datetime import datetime
from typing import List
from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.db.schemas.user import Roles
import enum

# Association tables
teacher_subject = Table(
    "teacher_subject",
    Base.metadata,
    Column("teacher_id", Integer, ForeignKey("teacher.id"), primary_key=True),
    Column("subject_id", Integer, ForeignKey("subject.id"), primary_key=True)
)

class User(Base):
    """User model for authentication"""
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[Roles] = mapped_column(Enum(Roles))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class School(Base):
    """School model"""
    __tablename__ = "school"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    classes: Mapped[List["Class"]] = relationship(back_populates="school")
    subjects: Mapped[List["Subject"]] = relationship(back_populates="school")
    teachers: Mapped[List["Teacher"]] = relationship(back_populates="school")

class Subject(Base):
    """Subject model"""
    __tablename__ = "subject"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    school_id: Mapped[int] = mapped_column(ForeignKey("school.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school: Mapped["School"] = relationship(back_populates="subjects")
    teachers: Mapped[List["Teacher"]] = relationship(secondary=teacher_subject, back_populates="subjects")
    grades: Mapped[List["Grade"]] = relationship(back_populates="subject")

class Teacher(Base):
    """Teacher model"""
    __tablename__ = "teacher"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[Roles] = mapped_column(Enum(Roles))
    school_id: Mapped[int] = mapped_column(ForeignKey("school.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school: Mapped["School"] = relationship(back_populates="teachers")
    subjects: Mapped[List["Subject"]] = relationship(secondary=teacher_subject, back_populates="teachers")
    homeroom_class: Mapped["Class"] = relationship(back_populates="homeroom_teacher")

class Class(Base):
    """Class model"""
    __tablename__ = "class"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    school_id: Mapped[int] = mapped_column(ForeignKey("school.id"))
    homeroom_teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school: Mapped["School"] = relationship(back_populates="classes")
    homeroom_teacher: Mapped["Teacher"] = relationship(back_populates="homeroom_class")
    students: Mapped[List["Student"]] = relationship(back_populates="class_")

class Student(Base):
    """Student model"""
    __tablename__ = "student"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    class_id: Mapped[int] = mapped_column(ForeignKey("class.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    class_: Mapped["Class"] = relationship(back_populates="students")
    grades: Mapped[List["Grade"]] = relationship(back_populates="student")
    attendance: Mapped[List["Attendance"]] = relationship(back_populates="student")

class Grade(Base):
    """Grade model"""
    __tablename__ = "grade"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"))
    value: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student: Mapped["Student"] = relationship(back_populates="grades")
    subject: Mapped["Subject"] = relationship(back_populates="grades")

class AttendanceStatus(enum.Enum):
    """Attendance status enum"""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"

class Attendance(Base):
    """Attendance model"""
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))
    date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(Enum(AttendanceStatus))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student: Mapped["Student"] = relationship(back_populates="attendance") 