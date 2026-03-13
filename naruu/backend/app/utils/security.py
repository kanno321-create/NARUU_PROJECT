"""JWT token management and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    sub: str
    username: str
    role: str
    type: str  # "access" or "refresh"
    exp: int
    iat: int


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": "access",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int, username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": "refresh",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_token_pair(user_id: int, username: str, role: str) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user_id, username, role),
        refresh_token=create_refresh_token(user_id, username, role),
    )


def decode_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return TokenPayload(**payload)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValidationError):
        return None


def verify_access_token(token: str) -> Optional[TokenPayload]:
    payload = decode_token(token)
    if payload and payload.type == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[TokenPayload]:
    payload = decode_token(token)
    if payload and payload.type == "refresh":
        return payload
    return None
