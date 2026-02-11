"""오케스트레이터 — AI 코어의 두뇌.

자연어 명령을 해석하여 적절한 플러그인으로 라우팅하고,
복합 워크플로우를 순차/병렬로 실행한다.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from naruu_core.event_bus import Event, EventBus
from naruu_core.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResult:
    """오케스트레이터 실행 결과."""

    success: bool
    plugin: str
    command: str
    result: dict[str, Any]
    error: str | None = None


class Orchestrator:
    """AI 오케스트레이터 — 자연어 명령 → 플러그인 라우팅 → 결과 통합.

    Claude API를 사용하여 자연어를 구조화된 명령으로 변환한다.
    API 키가 없는 경우 키워드 기반 폴백 라우팅을 사용한다.
    """

    def __init__(
        self,
        plugin_manager: PluginManager,
        event_bus: EventBus | None = None,
        anthropic_api_key: str | None = None,
    ) -> None:
        self._pm = plugin_manager
        self._event_bus = event_bus or plugin_manager.event_bus
        self._api_key = anthropic_api_key
        self._client: Any = None

        if self._api_key:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self._api_key)
            except ImportError:
                logger.warning("anthropic 패키지 미설치. 키워드 라우팅 사용.")

    async def route(self, natural_language: str) -> OrchestratorResult:
        """자연어 명령을 해석하여 플러그인으로 라우팅.

        Args:
            natural_language: 사용자의 자연어 명령.

        Returns:
            실행 결과.
        """
        parsed = await self._parse_command(natural_language)
        if parsed is None:
            return OrchestratorResult(
                success=False,
                plugin="",
                command="",
                result={},
                error="명령을 해석할 수 없습니다. "
                "등록된 플러그인이 없거나 매칭되는 기능이 없습니다.",
            )

        plugin_name, command, payload = parsed
        return await self.execute(plugin_name, command, payload)

    async def execute(
        self,
        plugin_name: str,
        command: str,
        payload: dict[str, Any] | None = None,
    ) -> OrchestratorResult:
        """특정 플러그인의 명령을 직접 실행.

        Args:
            plugin_name: 플러그인 이름.
            command: 명령 이름.
            payload: 명령 데이터.

        Returns:
            실행 결과.
        """
        payload = payload or {}

        await self._event_bus.publish(Event(
            event_type="orchestrator.execute.start",
            data={
                "plugin": plugin_name,
                "command": command,
            },
            source="orchestrator",
        ))

        try:
            result = await self._pm.execute(plugin_name, command, payload)

            await self._event_bus.publish(Event(
                event_type="orchestrator.execute.done",
                data={
                    "plugin": plugin_name,
                    "command": command,
                    "status": "ok",
                },
                source="orchestrator",
            ))

            return OrchestratorResult(
                success=True,
                plugin=plugin_name,
                command=command,
                result=result,
            )
        except Exception as e:
            logger.error("실행 실패: %s.%s — %s", plugin_name, command, e)

            await self._event_bus.publish(Event(
                event_type="orchestrator.execute.error",
                data={
                    "plugin": plugin_name,
                    "command": command,
                    "error": str(e),
                },
                source="orchestrator",
            ))

            return OrchestratorResult(
                success=False,
                plugin=plugin_name,
                command=command,
                result={},
                error=str(e),
            )

    async def execute_workflow(
        self, steps: list[dict[str, Any]]
    ) -> list[OrchestratorResult]:
        """여러 플러그인 명령을 순차 실행하는 워크플로우.

        Args:
            steps: 실행 단계 리스트.
                   각 단계: {"plugin": str, "command": str, "payload": dict}

        Returns:
            각 단계의 실행 결과 리스트.
        """
        results: list[OrchestratorResult] = []
        for step in steps:
            result = await self.execute(
                plugin_name=step["plugin"],
                command=step["command"],
                payload=step.get("payload", {}),
            )
            results.append(result)
            if not result.success:
                logger.warning(
                    "워크플로우 중단: %s.%s 실패",
                    step["plugin"],
                    step["command"],
                )
                break
        return results

    async def _parse_command(
        self, text: str
    ) -> tuple[str, str, dict[str, Any]] | None:
        """자연어를 (plugin_name, command, payload)로 변환.

        Claude API가 있으면 AI 파싱, 없으면 키워드 매칭.
        """
        if self._client:
            return await self._parse_with_ai(text)
        return self._parse_with_keywords(text)

    async def _parse_with_ai(
        self, text: str
    ) -> tuple[str, str, dict[str, Any]] | None:
        """Claude API로 자연어를 파싱."""
        plugins = self._pm.list_plugins()
        if not plugins:
            return None

        plugin_descriptions = []
        for p in plugins:
            plugin_descriptions.append(
                f"- {p.name}: {p.description or '설명 없음'} "
                f"[commands: {', '.join(p.capabilities)}]"
            )

        system_prompt = (
            "당신은 NARUU 플랫폼의 명령 라우터입니다.\n"
            "사용자의 자연어 명령을 분석하여 적절한 플러그인과 명령으로 변환하세요.\n\n"
            "등록된 플러그인:\n"
            + "\n".join(plugin_descriptions)
            + "\n\n"
            "반드시 다음 JSON 형식으로만 응답하세요:\n"
            '{"plugin": "플러그인이름", "command": "명령이름", "payload": {}}\n'
            "매칭되는 플러그인이 없으면 null을 반환하세요."
        )

        try:
            response = self._client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=256,
                system=system_prompt,
                messages=[{"role": "user", "content": text}],
            )
            content = response.content[0].text.strip()
            if content == "null":
                return None
            parsed = json.loads(content)
            return (parsed["plugin"], parsed["command"], parsed.get("payload", {}))
        except Exception:
            logger.warning("AI 파싱 실패, 키워드 폴백", exc_info=True)
            return self._parse_with_keywords(text)

    def _parse_with_keywords(
        self, text: str
    ) -> tuple[str, str, dict[str, Any]] | None:
        """키워드 매칭으로 자연어를 파싱 (폴백).

        텍스트에 포함된 키워드가 플러그인의 capability와 일치하면 라우팅.
        """
        text_lower = text.lower()
        plugins = self._pm.list_plugins()

        best_match: tuple[str, str] | None = None
        best_score = 0

        for p in plugins:
            if p.name.lower() in text_lower:
                for cap in p.capabilities:
                    return (p.name, cap, {"text": text})

            for cap in p.capabilities:
                score = 0
                cap_words = cap.lower().replace("-", " ").replace("_", " ").split()
                for word in cap_words:
                    if word in text_lower:
                        score += 1
                if score > best_score:
                    best_score = score
                    best_match = (p.name, cap)

        if best_match and best_score > 0:
            return (best_match[0], best_match[1], {"text": text})

        return None
