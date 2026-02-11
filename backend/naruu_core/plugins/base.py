"""플러그인 인터페이스 — 모든 NARUU 모듈이 구현해야 하는 계약."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PluginStatus(str, Enum):
    """플러그인 생명주기 상태."""

    REGISTERED = "registered"
    INITIALIZED = "initialized"
    RUNNING = "running"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass(frozen=True)
class PluginInfo:
    """플러그인 메타데이터."""

    name: str
    version: str
    description: str
    capabilities: list[str] = field(default_factory=list)
    status: PluginStatus = PluginStatus.REGISTERED


class NaruuPlugin(ABC):
    """모든 플러그인이 구현해야 하는 인터페이스.

    GitHub 오픈소스 도구를 연결할 때는 이 인터페이스를 감싸는
    어댑터를 작성하면 된다.

    Example::

        class MyAdapter(NaruuPlugin):
            def __init__(self, external_tool):
                self._tool = external_tool

            @property
            def name(self) -> str:
                return "my-adapter"

            async def execute(self, command, payload):
                return self._tool.run(command, **payload)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """플러그인 고유 이름 (예: 'content-automation', 'crm')."""

    @property
    @abstractmethod
    def version(self) -> str:
        """시맨틱 버전 (예: '0.1.0')."""

    @property
    def description(self) -> str:
        """플러그인 설명."""
        return ""

    @abstractmethod
    def capabilities(self) -> list[str]:
        """이 플러그인이 처리할 수 있는 명령 목록.

        오케스트레이터가 자연어 명령을 라우팅할 때 참조한다.
        """

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """플러그인 초기화. DB 연결, API 키 설정 등."""

    @abstractmethod
    async def execute(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        """명령 실행.

        Args:
            command: 실행할 명령 이름 (capabilities 중 하나).
            payload: 명령에 필요한 데이터.

        Returns:
            실행 결과 딕셔너리. 최소 {"status": "ok"} 포함.
        """

    @abstractmethod
    async def shutdown(self) -> None:
        """플러그인 정리. 리소스 해제, 연결 종료."""

    def info(self) -> PluginInfo:
        """플러그인 메타데이터 반환."""
        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            capabilities=self.capabilities(),
        )
