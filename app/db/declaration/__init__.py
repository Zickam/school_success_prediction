from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from ..engine import Base

# Association table for many-to-many relationship between users and classes
user_class_table = Table(
    "user_class",
    Base.metadata,
    Column("user_uuid", UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=True),
    Column("class_uuid", UUID(as_uuid=True), ForeignKey("class.uuid"), primary_key=True)
)

# Association table for parent-child relationships
parent_child = Table(
    "parent_child",
    Base.metadata,
    Column("parent_uuid", UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=True),
    Column("child_uuid", UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=True)
)

# Import models from main models.py
from ..models import User, School, Class, Subject, Grade

# Export all models
__all__ = [
    'User',
    'School',
    'Class',
    'Subject',
    'Grade',
    'user_class_table',
    'parent_child'
]