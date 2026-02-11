"""JWT 토큰 생성/검증."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt


class JWTHandler:
    """HS256 JWT 토큰 매니저."""

    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        expire_minutes: int = 60,
    ) -> None:
        if not secret:
            raise ValueError("JWT secret은 비어있을 수 없습니다.")
        self._secret = secret
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    def create_token(self, data: dict[str, Any]) -> str:
        """JWT 액세스 토큰 생성."""
        payload = data.copy()
        payload["exp"] = datetime.now(UTC) + timedelta(minutes=self._expire_minutes)
        payload["iat"] = datetime.now(UTC)
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict[str, Any]:
        """JWT 토큰 디코딩. 만료/변조 시 예외 발생."""
        result: dict[str, Any] = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        return result

    def create_refresh_token(self, data: dict[str, Any]) -> str:
        """리프레시 토큰 생성 (7일)."""
        payload = data.copy()
        payload["exp"] = datetime.now(UTC) + timedelta(days=7)
        payload["iat"] = datetime.now(UTC)
        payload["type"] = "refresh"
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)
