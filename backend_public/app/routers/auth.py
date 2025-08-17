from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth
from ..config import settings
from ..db import get_async_session
from .. import models
from ..auth import create_jwt
from ..schemas import TokenOut, UserOut
from datetime import datetime
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = settings.google_oauth_redirect
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback", response_model=TokenOut)
async def google_callback(request: Request, db: AsyncSession = Depends(get_async_session)):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")

    email = userinfo.get("email")
    name = userinfo.get("name")
    picture = userinfo.get("picture")
    sub = userinfo.get("sub")

    # upsert user
    result = await db.execute(
        select(models.AuthAccount).where(
            models.AuthAccount.provider == "google",
            models.AuthAccount.provider_account_id == sub,
        )
    )
    auth_account = result.scalar_one_or_none()
    if auth_account:
        user = await db.get(models.User, auth_account.user_id)
    else:
        result = await db.execute(select(models.User).where(models.User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            user = models.User(email=email, name=name, avatar_url=picture)
            db.add(user)
            await db.flush()
        auth_account = models.AuthAccount(user_id=user.id, provider="google", provider_account_id=sub, raw_profile=userinfo)
        db.add(auth_account)
    await db.flush()

    # issue jwt and session row
    access_token, exp = create_jwt(user.id, user.email)
    session = models.Session(user_id=user.id, jwt_id=access_token.split(".")[2][:32], created_at=datetime.utcnow(), expires_at=exp)
    db.add(session)
    await db.commit()

    return TokenOut(access_token=access_token)

@router.get("/me", response_model=UserOut)
async def me(user: models.User = Depends(get_current_user)):
    return user
