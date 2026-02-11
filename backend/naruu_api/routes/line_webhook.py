"""LINE 웹훅 라우터 — LINE Messaging API 이벤트 수신.

대표님 LINE으로 먼저 테스트 → 완성 후 야마다 나루미 LINE 전환.
환경변수 NARUU_LINE_CHANNEL_SECRET / NARUU_LINE_CHANNEL_ACCESS_TOKEN 변경만 하면 됨.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from naruu_api.deps import get_naruu_settings
from naruu_core.plugins.crm.line_client import LineClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/line", tags=["line"])

_line_client: LineClient | None = None


def get_line_client() -> LineClient:
    """LINE 클라이언트 싱글턴."""
    global _line_client
    if _line_client is None:
        settings = get_naruu_settings()
        if not settings.line_channel_secret or not settings.line_channel_access_token:
            raise RuntimeError(
                "LINE 설정 미완료. "
                "NARUU_LINE_CHANNEL_SECRET, NARUU_LINE_CHANNEL_ACCESS_TOKEN을 설정하세요."
            )
        _line_client = LineClient(
            channel_secret=settings.line_channel_secret,
            channel_access_token=settings.line_channel_access_token,
        )
    return _line_client


def reset_line_client() -> None:
    """테스트용 리셋."""
    global _line_client
    _line_client = None


@router.post("/webhook")
async def line_webhook(request: Request) -> dict[str, str]:
    """LINE 웹훅 수신 엔드포인트.

    LINE 플랫폼이 이벤트(메시지, 팔로우, 언팔로우 등)를 전송한다.
    서명 검증 → 이벤트 처리 → 200 OK 반환.
    """
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    # LINE 설정이 없으면 검증 스킵 (개발 모드)
    settings = get_naruu_settings()
    if settings.line_channel_secret and settings.line_channel_access_token:
        client = get_line_client()
        if not client.verify_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="유효하지 않은 LINE 서명입니다.",
            )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 JSON입니다.",
        ) from None

    events = payload.get("events", [])
    for event in events:
        await _handle_event(event)

    return {"status": "ok"}


async def _handle_event(event: dict[str, Any]) -> None:
    """LINE 이벤트 처리."""
    event_type = event.get("type", "")
    source = event.get("source", {})
    user_id = source.get("userId", "")

    if not user_id:
        return

    if event_type == "message":
        await _handle_message(event, user_id)
    elif event_type == "follow":
        logger.info("LINE follow: %s", user_id)
    elif event_type == "unfollow":
        logger.info("LINE unfollow: %s", user_id)
    else:
        logger.debug("LINE event ignored: %s", event_type)


async def _handle_message(event: dict[str, Any], user_id: str) -> None:
    """LINE 메시지 이벤트 처리."""
    message = event.get("message", {})
    msg_type = message.get("type", "")
    text = message.get("text", "")
    reply_token = event.get("replyToken", "")

    logger.info(
        "LINE message from %s: [%s] %s",
        user_id,
        msg_type,
        text[:50] if text else "(non-text)",
    )

    # LINE 설정이 있으면 자동 응답
    settings = get_naruu_settings()
    if (
        reply_token
        and settings.line_channel_secret
        and settings.line_channel_access_token
    ):
        try:
            client = get_line_client()
            await client.reply_message(
                reply_token,
                [
                    LineClient.text_message(
                        "NARUUへようこそ！\n"
                        "メッセージを受け取りました。\n"
                        "スタッフが確認後、ご連絡いたします。"
                    )
                ],
            )
        except Exception:
            logger.exception("LINE 자동응답 실패")
