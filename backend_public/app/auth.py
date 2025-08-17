from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException, status
from .config import settings
import uuid

ALGORITHM = "HS256"

def create_jwt(user_id: str, email: str | None, jwt_id: str | None = None) -> tuple[str, datetime]:
    if not jwt_id:
        jwt_id = uuid.uuid4().hex
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "jti": jwt_id,
        "iss": settings.jwt_issuer,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.app_secret, algorithm=ALGORITHM)
    return token, expire

def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.app_secret, algorithms=[ALGORITHM], options={"verify_aud": False})
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
