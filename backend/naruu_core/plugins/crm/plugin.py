"""CRM + LINE 플러그인 — NaruuPlugin 구현."""

from __future__ import annotations

from typing import Any

from naruu_core.plugins.base import NaruuPlugin
from naruu_core.plugins.crm.ai_responder import CustomerAIResponder


class Plugin(NaruuPlugin):
    """CRM 고객관리 + LINE 연동 플러그인.

    일본인 의료관광 고객의 라이프사이클을 관리한다.
    LINE → 문의(inquiry) → 예약(confirmed) → 완료(completed) → 후속관리.
    """

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._responder = CustomerAIResponder()

    @property
    def name(self) -> str:
        return "crm"

    @property
    def version(self) -> str:
        return "0.2.0"

    @property
    def description(self) -> str:
        return "CRM 고객관리 + LINE Messaging + AI 응답"

    def capabilities(self) -> list[str]:
        return [
            "customer.create",
            "customer.get",
            "customer.list",
            "customer.update",
            "booking.create",
            "booking.get",
            "booking.list",
            "booking.update",
            "interaction.create",
            "interaction.list",
            "line.send",
            "line.ai_respond",
        ]

    async def initialize(self, config: dict[str, Any]) -> None:
        """플러그인 초기화."""
        self._config = config

    async def execute(
        self, command: str, payload: dict[str, Any],
    ) -> dict[str, Any]:
        """명령 실행 — 오케스트레이터 라우팅 엔트리포인트."""
        if command == "line.ai_respond":
            message = payload.get("message", "")
            language = payload.get("language", "ja")
            name = payload.get("customer_name", "ゲスト")
            reply, cost = await self._responder.generate_response(
                customer_message=message,
                language=language,
                customer_name=name,
                config=self._config,
            )
            return {
                "status": "ok",
                "plugin": self.name,
                "command": command,
                "reply": reply,
                "cost_usd": cost,
            }

        return {
            "status": "ok",
            "plugin": self.name,
            "command": command,
            "message": f"CRM 명령 '{command}' 접수됨.",
        }

    async def shutdown(self) -> None:
        """플러그인 정리."""
        pass
