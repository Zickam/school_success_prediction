import os
from uuid import uuid4

from sqlalchemy import create_engine, Column, Integer, String, Uuid, ForeignKey, UUID, Float, DateTime, func
from sqlalchemy.orm import relationship

from ..engine import Base
from . import user_class_table


class School(Base):
    __tablename__ = "schools"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    facility_name = Column(String)


class Class(Base):
    __tablename__ = "classes"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    start_year = Column(Integer)
    class_name = Column(String)

    school_uuid = Column(UUID(as_uuid=True), ForeignKey('schools.uuid'))
    school = relationship("School")

    users = relationship("User", secondary=user_class_table, back_populates="classes")

    user_marks = relationship("UserClassMark", back_populates="user_class")


class UserClassMark(Base):
    __tablename__ = "user_class_marks"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"))
    class_uuid = Column(UUID(as_uuid=True), ForeignKey("classes.uuid"))
    mark = Column(Float)  # or Integer if marks are whole numbers
    discipline = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="class_marks")
    user_class = relationship("Class", back_populates="user_marks")

