"""플러그인 매니저 — 플러그인 등록/해제/조회/디스커버리."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

from naruu_core.event_bus import Event, EventBus
from naruu_core.plugins.base import NaruuPlugin, PluginInfo, PluginStatus

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """플러그인 관련 오류."""


class PluginManager:
    """플러그인 생명주기 관리.

    - register: 플러그인 등록 (붙이기)
    - unregister: 플러그인 해제 (떼기)
    - get: 이름으로 조회
    - list_plugins: 전체 목록
    - discover: 디렉토리 스캔 자동 등록
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._plugins: dict[str, NaruuPlugin] = {}
        self._statuses: dict[str, PluginStatus] = {}
        self._event_bus = event_bus or EventBus()

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    async def register(
        self, plugin: NaruuPlugin, config: dict[str, Any] | None = None
    ) -> PluginInfo:
        """플러그인을 등록하고 초기화.

        Args:
            plugin: NaruuPlugin 인터페이스 구현체.
            config: 초기화에 전달할 설정.

        Returns:
            등록된 플러그인 정보.

        Raises:
            PluginError: 이미 등록된 이름이거나 초기화 실패.
        """
        name = plugin.name
        if name in self._plugins:
            raise PluginError(f"플러그인 '{name}'은(는) 이미 등록되어 있습니다")

        try:
            await plugin.initialize(config or {})
            self._plugins[name] = plugin
            self._statuses[name] = PluginStatus.INITIALIZED
            logger.info("플러그인 등록: %s v%s", name, plugin.version)

            await self._event_bus.publish(Event(
                event_type="plugin.registered",
                data={"name": name, "version": plugin.version},
                source="plugin_manager",
            ))

            return plugin.info()
        except Exception as e:
            self._statuses[name] = PluginStatus.ERROR
            raise PluginError(f"플러그인 '{name}' 초기화 실패: {e}") from e

    async def unregister(self, name: str) -> None:
        """플러그인을 해제하고 정리.

        Args:
            name: 플러그인 이름.

        Raises:
            PluginError: 등록되지 않은 플러그인.
        """
        plugin = self._plugins.get(name)
        if plugin is None:
            raise PluginError(f"플러그인 '{name}'을(를) 찾을 수 없습니다")

        try:
            await plugin.shutdown()
        except Exception:
            logger.warning("플러그인 '%s' shutdown 중 오류 (무시)", name, exc_info=True)

        del self._plugins[name]
        self._statuses[name] = PluginStatus.SHUTDOWN
        logger.info("플러그인 해제: %s", name)

        await self._event_bus.publish(Event(
            event_type="plugin.unregistered",
            data={"name": name},
            source="plugin_manager",
        ))

    def get(self, name: str) -> NaruuPlugin | None:
        """이름으로 플러그인 조회."""
        return self._plugins.get(name)

    def list_plugins(self) -> list[PluginInfo]:
        """등록된 전체 플러그인 정보 목록."""
        result = []
        for name, plugin in self._plugins.items():
            info = plugin.info()
            result.append(PluginInfo(
                name=info.name,
                version=info.version,
                description=info.description,
                capabilities=info.capabilities,
                status=self._statuses.get(name, PluginStatus.REGISTERED),
            ))
        return result

    async def execute(
        self, plugin_name: str, command: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """특정 플러그인의 명령을 실행.

        Args:
            plugin_name: 플러그인 이름.
            command: 실행할 명령.
            payload: 명령 데이터.

        Returns:
            실행 결과.

        Raises:
            PluginError: 플러그인 미등록 또는 지원하지 않는 명령.
        """
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise PluginError(f"플러그인 '{plugin_name}'을(를) 찾을 수 없습니다")

        caps = plugin.capabilities()
        if command not in caps:
            raise PluginError(
                f"플러그인 '{plugin_name}'은(는) '{command}' 명령을 지원하지 않습니다. "
                f"사용 가능: {caps}"
            )

        self._statuses[plugin_name] = PluginStatus.RUNNING
        try:
            result = await plugin.execute(command, payload)
            self._statuses[plugin_name] = PluginStatus.INITIALIZED
            return result
        except Exception as e:
            self._statuses[plugin_name] = PluginStatus.ERROR
            raise PluginError(
                f"플러그인 '{plugin_name}' 명령 '{command}' 실행 실패: {e}"
            ) from e

    async def discover(self, directory: str | Path) -> list[PluginInfo]:
        """디렉토리를 스캔하여 플러그인을 자동 발견 및 등록.

        각 서브디렉토리에 plugin.py가 있고, 그 안에 NaruuPlugin의
        서브클래스 'Plugin'이 정의되어 있으면 자동 등록한다.

        Args:
            directory: 스캔할 플러그인 디렉토리.

        Returns:
            새로 등록된 플러그인 정보 목록.
        """
        directory = Path(directory)
        registered: list[PluginInfo] = []

        if not directory.is_dir():
            logger.warning("플러그인 디렉토리 없음: %s", directory)
            return registered

        for child in sorted(directory.iterdir()):
            if not child.is_dir():
                continue
            plugin_file = child / "plugin.py"
            if not plugin_file.exists():
                continue

            module_name = f"naruu_core.plugins.{child.name}.plugin"
            try:
                module = importlib.import_module(module_name)
                plugin_cls = getattr(module, "Plugin", None)
                if plugin_cls is None:
                    logger.warning("'Plugin' 클래스 없음: %s", module_name)
                    continue
                if not issubclass(plugin_cls, NaruuPlugin):
                    logger.warning("NaruuPlugin 미구현: %s", module_name)
                    continue

                plugin = plugin_cls()
                if plugin.name not in self._plugins:
                    info = await self.register(plugin)
                    registered.append(info)
            except Exception:
                logger.error("플러그인 로드 실패: %s", module_name, exc_info=True)

        return registered

    @property
    def count(self) -> int:
        """등록된 플러그인 수."""
        return len(self._plugins)
