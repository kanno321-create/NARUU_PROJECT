"""PluginManager 테스트."""

from __future__ import annotations

from typing import Any

import pytest

from naruu_core.event_bus import EventBus
from naruu_core.plugin_manager import PluginError, PluginManager
from naruu_core.plugins.base import NaruuPlugin, PluginStatus


class DummyPlugin(NaruuPlugin):
    """테스트용 플러그인."""

    def __init__(self, plugin_name: str = "dummy") -> None:
        self._name = plugin_name
        self._initialized = False
        self._shutdown = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "테스트용 더미 플러그인"

    def capabilities(self) -> list[str]:
        return ["test-command", "another-command"]

    async def initialize(self, config: dict[str, Any]) -> None:
        self._initialized = True

    async def execute(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "command": command, "payload": payload}

    async def shutdown(self) -> None:
        self._shutdown = True


class FailingPlugin(NaruuPlugin):
    """초기화에 실패하는 플러그인."""

    @property
    def name(self) -> str:
        return "failing"

    @property
    def version(self) -> str:
        return "0.0.1"

    def capabilities(self) -> list[str]:
        return ["fail"]

    async def initialize(self, config: dict[str, Any]) -> None:
        raise RuntimeError("초기화 실패!")

    async def execute(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def shutdown(self) -> None:
        pass


@pytest.fixture
def pm() -> PluginManager:
    return PluginManager(event_bus=EventBus())


@pytest.mark.asyncio
async def test_register(pm: PluginManager) -> None:
    """플러그인을 등록할 수 있다."""
    info = await pm.register(DummyPlugin())
    assert info.name == "dummy"
    assert info.version == "1.0.0"
    assert pm.count == 1


@pytest.mark.asyncio
async def test_register_duplicate_raises(pm: PluginManager) -> None:
    """같은 이름으로 중복 등록하면 에러."""
    await pm.register(DummyPlugin())
    with pytest.raises(PluginError, match="이미 등록"):
        await pm.register(DummyPlugin())


@pytest.mark.asyncio
async def test_register_failing_plugin_raises(pm: PluginManager) -> None:
    """초기화 실패 시 에러."""
    with pytest.raises(PluginError, match="초기화 실패"):
        await pm.register(FailingPlugin())


@pytest.mark.asyncio
async def test_unregister(pm: PluginManager) -> None:
    """플러그인을 해제할 수 있다."""
    plugin = DummyPlugin()
    await pm.register(plugin)
    await pm.unregister("dummy")
    assert pm.count == 0
    assert plugin._shutdown is True


@pytest.mark.asyncio
async def test_unregister_nonexistent_raises(pm: PluginManager) -> None:
    """존재하지 않는 플러그인 해제 시 에러."""
    with pytest.raises(PluginError, match="찾을 수 없습니다"):
        await pm.unregister("ghost")


@pytest.mark.asyncio
async def test_get(pm: PluginManager) -> None:
    """이름으로 플러그인을 조회할 수 있다."""
    await pm.register(DummyPlugin())
    plugin = pm.get("dummy")
    assert plugin is not None
    assert plugin.name == "dummy"

    assert pm.get("nonexistent") is None


@pytest.mark.asyncio
async def test_list_plugins(pm: PluginManager) -> None:
    """등록된 전체 플러그인 목록."""
    await pm.register(DummyPlugin("alpha"))
    await pm.register(DummyPlugin("beta"))
    plugins = pm.list_plugins()
    names = {p.name for p in plugins}
    assert names == {"alpha", "beta"}


@pytest.mark.asyncio
async def test_execute(pm: PluginManager) -> None:
    """플러그인 명령을 실행할 수 있다."""
    await pm.register(DummyPlugin())
    result = await pm.execute("dummy", "test-command", {"key": "value"})
    assert result["status"] == "ok"
    assert result["command"] == "test-command"
    assert result["payload"] == {"key": "value"}


@pytest.mark.asyncio
async def test_execute_unsupported_command(pm: PluginManager) -> None:
    """지원하지 않는 명령 실행 시 에러."""
    await pm.register(DummyPlugin())
    with pytest.raises(PluginError, match="지원하지 않습니다"):
        await pm.execute("dummy", "unsupported", {})


@pytest.mark.asyncio
async def test_execute_nonexistent_plugin(pm: PluginManager) -> None:
    """존재하지 않는 플러그인 실행 시 에러."""
    with pytest.raises(PluginError, match="찾을 수 없습니다"):
        await pm.execute("ghost", "cmd", {})


@pytest.mark.asyncio
async def test_plugin_status_tracking(pm: PluginManager) -> None:
    """플러그인 상태가 정확하게 추적된다."""
    await pm.register(DummyPlugin())
    plugins = pm.list_plugins()
    assert plugins[0].status == PluginStatus.INITIALIZED

    await pm.execute("dummy", "test-command", {})
    plugins = pm.list_plugins()
    assert plugins[0].status == PluginStatus.INITIALIZED


@pytest.mark.asyncio
async def test_event_published_on_register(pm: PluginManager) -> None:
    """플러그인 등록 시 이벤트가 발행된다."""
    events: list = []

    async def handler(event):
        events.append(event)

    pm.event_bus.subscribe("plugin.registered", handler)
    await pm.register(DummyPlugin())

    assert len(events) == 1
    assert events[0].data["name"] == "dummy"
