"""LINE Messaging API service wrapper."""

import hashlib
import hmac
import base64
from typing import Optional

import httpx

from app.config import get_settings

settings = get_settings()

LINE_API_BASE = "https://api.line.me/v2/bot"


class LineService:
    """Handles LINE Messaging API interactions."""

    def __init__(self):
        self.channel_access_token = settings.LINE_CHANNEL_ACCESS_TOKEN
        self.channel_secret = settings.LINE_CHANNEL_SECRET

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "application/json",
        }

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """Verify LINE webhook signature."""
        if not self.channel_secret:
            return False
        hash_value = hmac.new(
            self.channel_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).digest()
        expected = base64.b64encode(hash_value).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    async def reply_message(self, reply_token: str, text: str) -> dict:
        """Reply to a LINE message."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{LINE_API_BASE}/message/reply",
                headers=self._headers,
                json={
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": text}],
                },
            )
            return resp.json()

    async def push_message(self, user_id: str, text: str) -> dict:
        """Send a push message to a LINE user."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{LINE_API_BASE}/message/push",
                headers=self._headers,
                json={
                    "to": user_id,
                    "messages": [{"type": "text", "text": text}],
                },
            )
            return resp.json()

    async def get_profile(self, user_id: str) -> Optional[dict]:
        """Get LINE user profile."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{LINE_API_BASE}/profile/{user_id}",
                headers=self._headers,
            )
            if resp.status_code == 200:
                return resp.json()
            return None


def get_line_service() -> LineService:
    return LineService()
