import os
from collections import Counter

import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

engine = create_engine(os.getenv("DB_URL"), echo=True)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(sa.Uuid, primary_key=True)
    first_name = Column(String)

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name})>"

class Class(Base):
    """all classes of all time stored here"""
    __tablename__ = "classes"

    id = Column(sa.Uuid, primary_key=True)
    class_title = Column(String)
    start_year = Column(sa.Date)



class UserClass(Base):
    __tablename__ = "user_classes"

    users = relationship('User', secondary='project_users', back_populates='projects')





print(users)
