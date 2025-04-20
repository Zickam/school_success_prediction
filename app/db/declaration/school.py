import os
from uuid import uuid4

from sqlalchemy import create_engine, Column, Integer, String, Uuid, ForeignKey, UUID
from sqlalchemy.orm import relationship

from ..engine import Base


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