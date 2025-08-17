from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_async_session
from .auth import decode_jwt
from . import models
from .config import settings

BearerPrefix = "Bearer "

async def get_current_user(authorization: str | None = Header(default=None), db: AsyncSession = Depends(get_async_session)) -> models.User:
    if not authorization or not authorization.startswith(BearerPrefix):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization[len(BearerPrefix):]
    payload = decode_jwt(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    user = await db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    email = (user.email or "").lower()
    if settings.admin_emails and email in settings.admin_emails:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
