import os

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine(os.getenv("DB_URL"), echo=True)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    def __repr__(self):
        return f"<User(name={self.name}, email={self.email})>"

# Step 4: Create tables
Base.metadata.create_all(engine)

# Step 5: Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Step 6: Add new data
new_user = User(name='Alice', email='alice@example.com')
session.add(new_user)
session.commit()

# Step 7: Query data
users = session.query(User).all()
print(users)
