from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from .db import get_db
from .auth import decode_jwt
from . import models

BearerPrefix = "Bearer "

def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> models.User:
    if not authorization or not authorization.startswith(BearerPrefix):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization[len(BearerPrefix):]
    payload = decode_jwt(token)
    user_id = int(payload.get("sub"))
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
