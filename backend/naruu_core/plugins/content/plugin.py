"""콘텐츠 자동화 플러그인 — NaruuPlugin 구현."""

from __future__ import annotations

from typing import Any

from naruu_core.plugins.base import NaruuPlugin


class Plugin(NaruuPlugin):
    """콘텐츠 자동화 플러그인.

    파이프라인: Script(Claude) → Image(DALL-E) → Voice(VOICEVOX) → Video(FFmpeg) → Publish(YouTube)
    콘텐츠당 비용: $0.25-$0.86, 월 $51-215 (30-150개)
    """

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "content"

    @property
    def version(self) -> str:
        return "0.2.0"

    @property
    def description(self) -> str:
        return "콘텐츠 자동화 파이프라인 (동영상/블로그/SNS)"

    def capabilities(self) -> list[str]:
        return [
            "content.create",
            "content.get",
            "content.list",
            "content.update",
            "content.advance_pipeline",
            "schedule.create",
            "schedule.get",
            "schedule.list",
            "schedule.update",
            "schedule.delete",
        ]

    async def initialize(self, config: dict[str, Any]) -> None:
        self._config = config

    async def execute(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        """명령 실행 — DB 세션 없이도 동작하는 인터페이스.

        실제 DB CRUD는 FastAPI 라우트에서 ContentCRUD를 직접 사용.
        이 execute()는 오케스트레이터 경유 시 config 전달 + 상태 관리용.
        """
        if command == "content.advance_pipeline":
            return {
                "status": "ok",
                "plugin": self.name,
                "command": command,
                "config": {
                    "anthropic_api_key": self._config.get("anthropic_api_key", ""),
                    "ai_model": self._config.get("ai_model", "claude-sonnet-4-5-20250929"),
                    "ai_max_tokens": self._config.get("ai_max_tokens", 2048),
                    "ai_script_temperature": self._config.get(
                        "ai_script_temperature", 0.7
                    ),
                },
                "message": "advance_pipeline config 준비 완료.",
            }

        return {
            "status": "ok",
            "plugin": self.name,
            "command": command,
            "message": f"콘텐츠 명령 '{command}' 접수됨.",
        }

    async def shutdown(self) -> None:
        pass
