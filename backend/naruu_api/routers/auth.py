"""Authentication routes - JWT + role-based access"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import hashlib
import hmac
import secrets
import jwt

from naruu_api.config import config
from naruu_api.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str = "staff"
    language: str = "ja"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, hashed = stored.split(":")
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return hmac.compare_digest(check.hex(), hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dependency: extract and validate current user from JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    result = await db.execute(
        text("SELECT id, username, name, role, language, status FROM naruu.users WHERE id = :id"),
        {"id": user_id},
    )
    user = result.mappings().first()
    if user is None or user["status"] != "active":
        raise credentials_exception
    return dict(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT id, username, name, role, language, password_hash, status FROM naruu.users WHERE username = :username"),
        {"username": form_data.username},
    )
    user = result.mappings().first()

    if not user or user["status"] != "active":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Update last login
    await db.execute(
        text("UPDATE naruu.users SET last_login = NOW() WHERE id = :id"),
        {"id": str(user["id"])},
    )
    await db.commit()

    token = create_access_token(data={"sub": str(user["id"]), "role": user["role"]})

    return TokenResponse(
        access_token=token,
        expires_in=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user["id"]),
            "username": user["username"],
            "name": user["name"],
            "role": user["role"],
            "language": user["language"],
        },
    )


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/users", status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")

    password_hash = hash_password(user_data.password)
    result = await db.execute(
        text("""
            INSERT INTO naruu.users (username, password_hash, name, role, language)
            VALUES (:username, :password_hash, :name, :role, :language)
            RETURNING id, username, name, role, language
        """),
        {
            "username": user_data.username,
            "password_hash": password_hash,
            "name": user_data.name,
            "role": user_data.role,
            "language": user_data.language,
        },
    )
    await db.commit()
    new_user = result.mappings().first()
    return dict(new_user)
