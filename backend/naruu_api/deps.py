"""의존성 주입 — FastAPI Depends용 싱글턴."""

from __future__ import annotations

from naruu_core.config import NaruuSettings, get_settings
from naruu_core.event_bus import EventBus
from naruu_core.orchestrator import Orchestrator
from naruu_core.plugin_manager import PluginManager

_event_bus: EventBus | None = None
_plugin_manager: PluginManager | None = None
_orchestrator: Orchestrator | None = None
_settings: NaruuSettings | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def get_plugin_manager() -> PluginManager:
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager(event_bus=get_event_bus())
    return _plugin_manager


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        settings = get_naruu_settings()
        _orchestrator = Orchestrator(
            plugin_manager=get_plugin_manager(),
            event_bus=get_event_bus(),
            anthropic_api_key=settings.anthropic_api_key or None,
        )
    return _orchestrator


def get_naruu_settings() -> NaruuSettings:
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


def reset_all() -> None:
    """테스트용 전역 상태 리셋."""
    global _event_bus, _plugin_manager, _orchestrator, _settings
    _event_bus = None
    _plugin_manager = None
    _orchestrator = None
    _settings = None
