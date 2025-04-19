import os

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

from ..engine import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name})>"

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
