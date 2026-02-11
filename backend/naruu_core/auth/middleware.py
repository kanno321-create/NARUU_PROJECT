"""인증 미들웨어 — FastAPI Depends용."""

from __future__ import annotations

from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from naruu_core.auth.jwt_handler import JWTHandler

_security = HTTPBearer(auto_error=False)

_jwt_handler: JWTHandler | None = None


def get_jwt_handler() -> JWTHandler:
    """JWT 핸들러 싱글턴."""
    global _jwt_handler
    if _jwt_handler is None:
        from naruu_api.deps import get_naruu_settings

        settings = get_naruu_settings()
        if not settings.jwt_secret:
            raise RuntimeError("JWT_SECRET이 설정되지 않았습니다.")
        _jwt_handler = JWTHandler(
            secret=settings.jwt_secret,
            expire_minutes=settings.jwt_expire_minutes,
        )
    return _jwt_handler


def reset_jwt_handler() -> None:
    """테스트용 리셋."""
    global _jwt_handler
    _jwt_handler = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> dict[str, Any]:
    """현재 인증된 사용자 정보 반환.

    Returns:
        JWT payload (sub, email, role 등).
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다.",
        )

    try:
        handler = get_jwt_handler()
        payload = handler.decode_token(credentials.credentials)
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다.",
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        ) from None


async def require_admin(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """관리자 권한 확인."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )
    return user
