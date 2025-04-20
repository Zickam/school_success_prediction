import os

import enum
from sqlalchemy import create_engine, Column, Integer, String, UUID, Uuid, Enum
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker
from uuid import uuid4

from ..engine import Base

from ..schemas.user import Roles


class User(Base):
    __tablename__ = 'users'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chat_id = Column(Integer, unique=True)
    role = Column(Enum(Roles))
    name = Column(String)

    # def __repr__(self):
    #     return f"<User(id={self.id}, name={self.name})>"
