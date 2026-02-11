"""이벤트 버스 — 모듈 간 느슨한 결합을 위한 이벤트 발행/구독 시스템.

예약 이벤트가 발생하면 콘텐츠 생성 플러그인이 자동으로 트리거되는 식.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

EventHandler = Callable[["Event"], Coroutine[Any, Any, None]]


@dataclass(frozen=True)
class Event:
    """이벤트 데이터."""

    event_type: str
    data: dict[str, Any]
    source: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventBus:
    """비동기 이벤트 발행/구독 시스템."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []
        self._max_history = 100

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """이벤트 타입에 핸들러를 구독."""
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.info("이벤트 구독: %s → %s", event_type, handler.__qualname__)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """이벤트 타입에서 핸들러를 구독 해제."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)
            logger.info("이벤트 구독 해제: %s → %s", event_type, handler.__qualname__)

    async def publish(self, event: Event) -> list[dict[str, Any]]:
        """이벤트를 발행하고 모든 구독 핸들러를 실행.

        Returns:
            각 핸들러의 실행 결과 리스트.
        """
        self._record(event)
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            logger.debug("이벤트 '%s'에 구독자 없음", event.event_type)
            return []

        logger.info(
            "이벤트 발행: %s → %d개 핸들러",
            event.event_type,
            len(handlers),
        )

        results: list[dict[str, Any]] = []
        tasks = [self._safe_call(h, event) for h in handlers]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        for handler, outcome in zip(handlers, outcomes, strict=False):
            if isinstance(outcome, Exception):
                logger.error(
                    "핸들러 실패: %s — %s",
                    handler.__qualname__,
                    outcome,
                )
                results.append({
                    "handler": handler.__qualname__,
                    "status": "error",
                    "error": str(outcome),
                })
            else:
                results.append({
                    "handler": handler.__qualname__,
                    "status": "ok",
                })

        return results

    def get_handlers(self, event_type: str) -> list[EventHandler]:
        """특정 이벤트 타입의 구독 핸들러 목록."""
        return list(self._handlers.get(event_type, []))

    def get_history(self, limit: int = 10) -> list[Event]:
        """최근 이벤트 히스토리."""
        return self._history[-limit:]

    def clear(self) -> None:
        """모든 구독과 히스토리 초기화."""
        self._handlers.clear()
        self._history.clear()

    @staticmethod
    async def _safe_call(handler: EventHandler, event: Event) -> None:
        """핸들러를 안전하게 호출."""
        await handler(event)

    def _record(self, event: Event) -> None:
        """이벤트 히스토리에 기록."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]
