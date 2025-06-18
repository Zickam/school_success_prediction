import os

import enum
from sqlalchemy import create_engine, Column, Integer, String, UUID, Uuid, Enum
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from uuid import uuid4

from ..engine import Base

from ..schemas.user import Roles


from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from . import user_class_table



class User(Base):
    __tablename__ = 'users'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chat_id = Column(Integer, unique=True)
    role = Column(Enum(Roles))
    name = Column(String)

    classes = relationship("Class", secondary=user_class_table, back_populates="users")

    class_marks = relationship("UserClassMark", back_populates="user")
