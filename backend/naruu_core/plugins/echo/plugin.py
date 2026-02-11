"""Echo 플러그인 — 시스템 검증 및 테스트용.

입력을 그대로 반환하여 플러그인 아키텍처가 정상 동작하는지 확인한다.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from naruu_core.plugins.base import NaruuPlugin


class Plugin(NaruuPlugin):
    """Echo 플러그인 — 입력을 그대로 반환."""

    @property
    def name(self) -> str:
        return "echo"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "시스템 검증용 에코 플러그인. 입력을 그대로 반환합니다."

    def capabilities(self) -> list[str]:
        return ["echo", "ping", "info"]

    async def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._initialized_at = datetime.now(UTC)

    async def execute(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        if command == "echo":
            return {
                "status": "ok",
                "echo": payload,
            }
        if command == "ping":
            return {
                "status": "ok",
                "pong": True,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        if command == "info":
            return {
                "status": "ok",
                "name": self.name,
                "version": self.version,
                "initialized_at": self._initialized_at.isoformat(),
                "capabilities": self.capabilities(),
            }
        return {"status": "error", "message": f"알 수 없는 명령: {command}"}

    async def shutdown(self) -> None:
        pass
