import os

from sqlalchemy import create_engine, Column, Integer, String, UUID, Uuid
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker
import uuid

from ..engine import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(Integer, unique=True)
    role = Column(String)
    name = Column(String)

    # def __repr__(self):
    #     return f"<User(id={self.id}, name={self.name})>"

# Step 5: Create a session
# Session = sessionmaker(bind=engine)
# session = Session()
#
# # Step 6: Add new data
# new_user = User(name='Alice')
# session.add(new_user)
# session.commit()
#
# # Step 7: Query data
# users = session.query(User).all()
# print(users)
