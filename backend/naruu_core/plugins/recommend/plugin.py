"""관광 추천 플러그인 — NaruuPlugin 구현."""

from __future__ import annotations

from typing import Any

from naruu_core.plugins.base import NaruuPlugin


class Plugin(NaruuPlugin):
    """관광 추천 엔진 플러그인.

    스코어링: category_match + tag_match + rating + popularity + budget_fit
    대구 의료관광/뷰티/관광지/맛집/쇼핑 추천.
    """

    @property
    def name(self) -> str:
        return "recommend"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "관광 추천 엔진 (의료/뷰티/관광/맛집/쇼핑)"

    def capabilities(self) -> list[str]:
        return [
            "spot.create",
            "spot.get",
            "spot.list",
            "spot.update",
            "recommend.search",
        ]

    async def initialize(self, config: dict[str, Any]) -> None:
        self._config = config

    async def execute(
        self, command: str, payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": "ok",
            "plugin": self.name,
            "command": command,
            "message": f"추천 명령 '{command}' 접수됨.",
        }

    async def shutdown(self) -> None:
        pass
