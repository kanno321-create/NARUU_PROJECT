"""거래처 관리 플러그인 — NaruuPlugin 구현."""

from __future__ import annotations

from typing import Any

from naruu_core.plugins.base import NaruuPlugin


class Plugin(NaruuPlugin):
    """거래처/클리닉 관리 플러그인.

    NARUU 플랫폼의 의료/미용/관광 거래처를 관리한다.
    CRUD는 PartnerCRUD 서비스를 통해 수행하며,
    이 플러그인은 오케스트레이터 라우팅 인터페이스를 제공한다.
    """

    @property
    def name(self) -> str:
        return "partner"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "거래처/클리닉 관리 (medical, beauty, tourism)"

    def capabilities(self) -> list[str]:
        return [
            "partner.create",
            "partner.get",
            "partner.list",
            "partner.update",
            "partner.delete",
            "service.create",
            "service.get",
            "service.list",
            "service.update",
            "service.delete",
        ]

    async def initialize(self, config: dict[str, Any]) -> None:
        """플러그인 초기화."""
        self._config = config

    async def execute(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        """명령 실행 — 오케스트레이터 라우팅 엔트리포인트.

        실제 DB 작업은 REST 라우트에서 PartnerCRUD를 직접 사용한다.
        이 메서드는 오케스트레이터가 자연어 명령을 라우팅할 때 사용.
        """
        return {
            "status": "ok",
            "plugin": self.name,
            "command": command,
            "message": f"거래처 명령 '{command}' 접수됨. REST API로 처리하세요.",
        }

    async def shutdown(self) -> None:
        """플러그인 정리."""
        pass
