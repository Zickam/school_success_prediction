import os
from typing import Annotated

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from fastapi import Depends, FastAPI, HTTPException, Query


engine = create_async_engine(os.getenv("DB_URL"), echo=True)

Base = declarative_base()

def getSession():
    with sessionmaker(bind=engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(getSession)]