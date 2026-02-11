"""LINE Messaging API 클라이언트.

httpx 기반 경량 클라이언트. line-bot-sdk 의존성 불필요.
대표님 LINE → 테스트 완료 후 → 야마다 나루미 LINE 전환은 환경변수만 변경.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from base64 import b64encode
from typing import Any

import httpx

logger = logging.getLogger(__name__)

LINE_API_BASE = "https://api.line.me/v2/bot"


class LineClient:
    """LINE Messaging API 클라이언트."""

    def __init__(self, channel_secret: str, channel_access_token: str) -> None:
        if not channel_secret or not channel_access_token:
            raise ValueError("LINE channel_secret과 channel_access_token은 필수입니다.")
        self._secret = channel_secret
        self._token = channel_access_token
        self._http = httpx.AsyncClient(
            base_url=LINE_API_BASE,
            headers={"Authorization": f"Bearer {channel_access_token}"},
            timeout=30.0,
        )

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """웹훅 서명 검증 (HMAC-SHA256)."""
        digest = hmac.new(
            self._secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).digest()
        expected = b64encode(digest).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    async def reply_message(self, reply_token: str, messages: list[dict[str, Any]]) -> bool:
        """LINE 메시지 답장."""
        resp = await self._http.post(
            "/message/reply",
            json={"replyToken": reply_token, "messages": messages},
        )
        if resp.status_code != 200:
            logger.error("LINE reply 실패: %s %s", resp.status_code, resp.text)
            return False
        return True

    async def push_message(self, to: str, messages: list[dict[str, Any]]) -> bool:
        """LINE 메시지 발송 (푸시)."""
        resp = await self._http.post(
            "/message/push",
            json={"to": to, "messages": messages},
        )
        if resp.status_code != 200:
            logger.error("LINE push 실패: %s %s", resp.status_code, resp.text)
            return False
        return True

    async def get_profile(self, user_id: str) -> dict[str, Any] | None:
        """LINE 유저 프로필 조회."""
        resp = await self._http.get(f"/profile/{user_id}")
        if resp.status_code != 200:
            logger.warning("LINE profile 조회 실패: %s", user_id)
            return None
        result: dict[str, Any] = resp.json()
        return result

    @staticmethod
    def text_message(text: str) -> dict[str, str]:
        """텍스트 메시지 헬퍼."""
        return {"type": "text", "text": text}

    async def close(self) -> None:
        """HTTP 클라이언트 종료."""
        await self._http.aclose()
