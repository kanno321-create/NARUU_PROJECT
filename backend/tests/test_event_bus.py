"""EventBus 테스트."""

from __future__ import annotations

import pytest

from naruu_core.event_bus import Event, EventBus


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.mark.asyncio
async def test_publish_without_subscribers(bus: EventBus) -> None:
    """구독자 없는 이벤트 발행은 빈 결과."""
    event = Event(event_type="test.event", data={"key": "value"})
    results = await bus.publish(event)
    assert results == []


@pytest.mark.asyncio
async def test_subscribe_and_publish(bus: EventBus) -> None:
    """구독 후 이벤트 발행 시 핸들러가 호출된다."""
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe("test.event", handler)
    event = Event(event_type="test.event", data={"msg": "hello"})
    results = await bus.publish(event)

    assert len(received) == 1
    assert received[0].data["msg"] == "hello"
    assert results[0]["status"] == "ok"


@pytest.mark.asyncio
async def test_unsubscribe(bus: EventBus) -> None:
    """구독 해제 후 이벤트가 전달되지 않는다."""
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe("test.event", handler)
    bus.unsubscribe("test.event", handler)

    await bus.publish(Event(event_type="test.event", data={}))
    assert len(received) == 0


@pytest.mark.asyncio
async def test_multiple_handlers(bus: EventBus) -> None:
    """같은 이벤트에 여러 핸들러 등록."""
    calls: list[str] = []

    async def handler_a(event: Event) -> None:
        calls.append("a")

    async def handler_b(event: Event) -> None:
        calls.append("b")

    bus.subscribe("multi", handler_a)
    bus.subscribe("multi", handler_b)
    await bus.publish(Event(event_type="multi", data={}))

    assert "a" in calls
    assert "b" in calls


@pytest.mark.asyncio
async def test_handler_error_does_not_block_others(bus: EventBus) -> None:
    """하나의 핸들러 실패가 다른 핸들러를 막지 않는다."""
    calls: list[str] = []

    async def failing_handler(event: Event) -> None:
        raise RuntimeError("테스트 에러")

    async def ok_handler(event: Event) -> None:
        calls.append("ok")

    bus.subscribe("err", failing_handler)
    bus.subscribe("err", ok_handler)

    results = await bus.publish(Event(event_type="err", data={}))
    assert "ok" in calls
    assert results[0]["status"] == "error"
    assert results[1]["status"] == "ok"


@pytest.mark.asyncio
async def test_event_history(bus: EventBus) -> None:
    """이벤트 히스토리가 기록된다."""
    await bus.publish(Event(event_type="a", data={"n": 1}))
    await bus.publish(Event(event_type="b", data={"n": 2}))

    history = bus.get_history(limit=10)
    assert len(history) == 2
    assert history[0].event_type == "a"
    assert history[1].event_type == "b"


@pytest.mark.asyncio
async def test_duplicate_subscribe_ignored(bus: EventBus) -> None:
    """같은 핸들러 중복 등록은 무시된다."""
    calls: list[str] = []

    async def handler(event: Event) -> None:
        calls.append("x")

    bus.subscribe("dup", handler)
    bus.subscribe("dup", handler)

    await bus.publish(Event(event_type="dup", data={}))
    assert len(calls) == 1


def test_get_handlers(bus: EventBus) -> None:
    """구독된 핸들러 목록을 조회할 수 있다."""

    async def handler(event: Event) -> None:
        pass

    bus.subscribe("test", handler)
    handlers = bus.get_handlers("test")
    assert len(handlers) == 1


def test_clear(bus: EventBus) -> None:
    """clear로 모든 구독과 히스토리를 초기화."""

    async def handler(event: Event) -> None:
        pass

    bus.subscribe("test", handler)
    bus.clear()
    assert bus.get_handlers("test") == []
    assert bus.get_history() == []
