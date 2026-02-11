"""인증 라우터 — 로그인, 회원가입, 토큰 갱신."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_api.deps import get_db_session
from naruu_core.auth.jwt_handler import JWTHandler
from naruu_core.auth.middleware import get_current_user, get_jwt_handler, require_admin
from naruu_core.auth.password import hash_password, verify_password
from naruu_core.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


# -- Request/Response 스키마 --


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "staff"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool


class RefreshRequest(BaseModel):
    refresh_token: str


# -- 라우트 --


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    req: RegisterRequest,
    _admin: dict = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """사용자 등록 (관리자 전용)."""
    existing = await session.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 등록된 이메일입니다.",
        )

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=req.role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
) -> TokenResponse:
    """로그인 → JWT 토큰 발급."""
    result = await session.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다.",
        )

    token_data = {"sub": user.id, "email": user.email, "role": user.role}
    return TokenResponse(
        access_token=jwt_handler.create_token(token_data),
        refresh_token=jwt_handler.create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """현재 인증된 사용자 정보."""
    result = await session.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    req: RefreshRequest,
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
) -> TokenResponse:
    """리프레시 토큰으로 새 액세스 토큰 발급."""
    import jwt as pyjwt

    try:
        payload = jwt_handler.decode_token(req.refresh_token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="리프레시 토큰이 만료되었습니다.") from None
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.") from None

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="리프레시 토큰이 아닙니다.")

    token_data = {"sub": payload["sub"], "email": payload["email"], "role": payload["role"]}
    return TokenResponse(
        access_token=jwt_handler.create_token(token_data),
        refresh_token=jwt_handler.create_refresh_token(token_data),
    )
