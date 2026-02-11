"""Orchestrator 테스트."""

from __future__ import annotations

from typing import Any

import pytest

from naruu_core.event_bus import EventBus
from naruu_core.orchestrator import Orchestrator
from naruu_core.plugin_manager import PluginManager
from naruu_core.plugins.base import NaruuPlugin


class MockPlugin(NaruuPlugin):
    """테스트용 플러그인."""

    @property
    def name(self) -> str:
        return "mock-tool"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "테스트용 도구"

    def capabilities(self) -> list[str]:
        return ["generate", "analyze"]

    async def initialize(self, config: dict[str, Any]) -> None:
        pass

    async def execute(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        if command == "generate":
            return {"status": "ok", "generated": True, "input": payload}
        if command == "analyze":
            return {"status": "ok", "analysis": "complete"}
        return {"status": "error"}

    async def shutdown(self) -> None:
        pass


@pytest.fixture
async def orch() -> Orchestrator:
    bus = EventBus()
    pm = PluginManager(event_bus=bus)
    await pm.register(MockPlugin())
    return Orchestrator(plugin_manager=pm, event_bus=bus)


@pytest.mark.asyncio
async def test_direct_execute(orch: Orchestrator) -> None:
    """플러그인을 직접 실행할 수 있다."""
    result = await orch.execute("mock-tool", "generate", {"topic": "대구 관광"})
    assert result.success is True
    assert result.plugin == "mock-tool"
    assert result.command == "generate"
    assert result.result["generated"] is True


@pytest.mark.asyncio
async def test_execute_nonexistent_plugin(orch: Orchestrator) -> None:
    """존재하지 않는 플러그인 실행 시 실패."""
    result = await orch.execute("ghost", "cmd", {})
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_keyword_routing(orch: Orchestrator) -> None:
    """키워드 매칭으로 자연어가 플러그인에 라우팅된다."""
    result = await orch.route("mock-tool로 뭔가 해줘")
    assert result.success is True
    assert result.plugin == "mock-tool"


@pytest.mark.asyncio
async def test_routing_no_match(orch: Orchestrator) -> None:
    """매칭되는 플러그인이 없으면 실패."""
    bus = EventBus()
    pm = PluginManager(event_bus=bus)
    empty_orch = Orchestrator(plugin_manager=pm, event_bus=bus)

    result = await empty_orch.route("아무거나 해줘")
    assert result.success is False


@pytest.mark.asyncio
async def test_workflow_execution(orch: Orchestrator) -> None:
    """워크플로우(다단계) 실행."""
    steps = [
        {"plugin": "mock-tool", "command": "generate", "payload": {"n": 1}},
        {"plugin": "mock-tool", "command": "analyze", "payload": {}},
    ]
    results = await orch.execute_workflow(steps)
    assert len(results) == 2
    assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_workflow_stops_on_failure(orch: Orchestrator) -> None:
    """워크플로우 중 실패하면 중단."""
    steps = [
        {"plugin": "ghost", "command": "fail", "payload": {}},
        {"plugin": "mock-tool", "command": "generate", "payload": {}},
    ]
    results = await orch.execute_workflow(steps)
    assert len(results) == 1
    assert results[0].success is False


@pytest.mark.asyncio
async def test_events_published_on_execute(orch: Orchestrator) -> None:
    """실행 시 이벤트가 발행된다."""
    events: list = []

    async def handler(event):
        events.append(event)

    orch._event_bus.subscribe("orchestrator.execute.start", handler)
    orch._event_bus.subscribe("orchestrator.execute.done", handler)

    await orch.execute("mock-tool", "generate", {})

    types = [e.event_type for e in events]
    assert "orchestrator.execute.start" in types
    assert "orchestrator.execute.done" in types
