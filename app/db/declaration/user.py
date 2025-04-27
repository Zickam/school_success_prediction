from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, Integer, String, UUID, Enum, DateTime
from sqlalchemy.orm import relationship

from ..engine import Base
from ..schemas.user import Roles
from . import user_class_table

class User(Base):
    __tablename__ = 'users'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chat_id = Column(Integer, unique=True)
    role = Column(Enum(Roles))
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    classes = relationship("Class", secondary=user_class_table, back_populates="users")
    grades = relationship("Grade", back_populates="user")
