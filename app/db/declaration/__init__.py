from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from ..engine import Base, engine, getSession
user_class_table = Table(
    "user_class",
    Base.metadata,
    Column("user_uuid", UUID(as_uuid=True), ForeignKey("users.uuid"), primary_key=True),
    Column("class_uuid", UUID(as_uuid=True), ForeignKey("classes.uuid"), primary_key=True)
)


from . import user, school