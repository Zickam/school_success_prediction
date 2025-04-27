from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, Integer, String, ForeignKey, UUID, DateTime, Float
from sqlalchemy.orm import relationship

from ..engine import Base
from . import user_class_table


class School(Base):
    __tablename__ = "schools"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    facility_name = Column(String)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    classes = relationship("Class", back_populates="school")


class Class(Base):
    __tablename__ = "classes"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    start_year = Column(Integer)
    class_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    school_uuid = Column(UUID(as_uuid=True), ForeignKey('schools.uuid'))
    school = relationship("School", back_populates="classes")
    users = relationship("User", secondary=user_class_table, back_populates="classes")
    subjects = relationship("Subject", back_populates="class_")


class Subject(Base):
    __tablename__ = "subjects"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class_uuid = Column(UUID(as_uuid=True), ForeignKey('classes.uuid'))
    class_ = relationship("Class", back_populates="subjects")
    grades = relationship("Grade", back_populates="subject")


class Grade(Base):
    __tablename__ = "grades"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    value = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    subject_uuid = Column(UUID(as_uuid=True), ForeignKey('subjects.uuid'))
    
    user = relationship("User", back_populates="grades")
    subject = relationship("Subject", back_populates="grades")