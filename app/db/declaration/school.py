import os

from sqlalchemy import create_engine, Column, Integer, String, Uuid, ForeignKey
from sqlalchemy.orm import relationship

from ..engine import Base


class School(Base):
    __tablename__ = "schools"

    id = Column(Uuid, primary_key=True)
    facility_name = Column(String)


class Class(Base):
    __tablename__ = "classes"

    id = Column(Uuid, primary_key=True)
    start_year = Column(Integer)
    class_name = Column(String)

    school_id = Column(Integer, ForeignKey('schools.id'))
    school = relationship("School")