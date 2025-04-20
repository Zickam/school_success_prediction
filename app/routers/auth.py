from __future__ import annotations
import os
import logging
import datetime

from fastapi import APIRouter, Depends
from fastapi import Response, Request, Query
from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from ..auth_dependency import SECRET_KEY, ALGORITHM

router = APIRouter(tags=["Auth"])

@router.post("/token")
def login(username: str = Form(), password: str = Form()):
    # Dummy check — replace with real user verification
    if username != os.getenv("AUTH_USERNAME") or password != os.getenv("AUTH_PASSWORD"):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    to_encode = {
        "sub": username,
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=int(os.getenv("AUTH_EXPIRATION")))
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}