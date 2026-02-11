"""이벤트 배선 테스트 — 서비스 → EventBus → 핸들러 연동 검증."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import respx
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_api.main import (
    _on_booking_status_changed,
    _on_customer_created,
    _on_pipeline_advanced,
)
from naruu_core.event_bus import Event, EventBus
from naruu_core.plugins.content.schemas import ContentCreate
from naruu_core.plugins.content.service import ContentCRUD
from naruu_core.plugins.crm.schemas import (
    BookingCreate,
    BookingUpdate,
    CustomerCreate,
)
from naruu_core.plugins.crm.service import CrmCRUD

# ── 핸들러 단위 테스트 ─────────────────────────────────────


class TestEventHandlers:
    """main.py에 등록된 이벤트 핸들러 단위 테스트."""

    @pytest.mark.asyncio
    async def test_on_pipeline_advanced_logs(self) -> None:
        """파이프라인 진행 핸들러가 예외 없이 실행된다."""
        event = Event(
            event_type="content.pipeline.advanced",
            data={
                "content_id": "c1",
                "from_stage": "pending",
                "to_stage": "script",
                "cost_usd": 0.0,
            },
            source="content_service",
        )
        await _on_pipeline_advanced(event)

    @pytest.mark.asyncio
    async def test_on_customer_created_logs(self) -> None:
        """고객 생성 핸들러가 예외 없이 실행된다."""
        event = Event(
            event_type="customer.created",
            data={
                "customer_id": "cust1",
                "line_user_id": "U123",
                "display_name": "テスト太郎",
            },
            source="crm_service",
        )
        await _on_customer_created(event)

    @pytest.mark.asyncio
    async def test_on_booking_status_changed_logs(self) -> None:
        """예약 상태 변경 핸들러가 예외 없이 실행된다."""
        event = Event(
            event_type="booking.status_changed",
            data={
                "booking_id": "b1",
                "customer_id": "cust1",
                "old_status": "inquiry",
                "new_status": "confirmed",
            },
            source="crm_service",
        )
        await _on_booking_status_changed(event)


# ── 이벤트 발행 통합 테스트 (CRM) ─────────────────────────


class TestCrmEventPublishing:
    """CRM 서비스가 이벤트를 올바르게 발행하는지 검증."""

    @pytest.mark.asyncio
    async def test_create_customer_publishes_event(
        self, db_session: AsyncSession,
    ) -> None:
        """고객 생성 시 customer.created 이벤트가 발행된다."""
        bus = EventBus()
        received: list[Event] = []

        async def capture(event: Event) -> None:
            received.append(event)

        bus.subscribe("customer.created", capture)

        crud = CrmCRUD(db_session, event_bus=bus)
        customer = await crud.create_customer(
            CustomerCreate(display_name="田中花子"),
        )

        assert len(received) == 1
        assert received[0].event_type == "customer.created"
        assert received[0].data["customer_id"] == customer.id
        assert received[0].data["display_name"] == "田中花子"
        assert received[0].source == "crm_service"

    @pytest.mark.asyncio
    async def test_update_booking_publishes_status_change(
        self, db_session: AsyncSession,
    ) -> None:
        """예약 상태 변경 시 booking.status_changed 이벤트가 발행된다."""
        bus = EventBus()
        received: list[Event] = []

        async def capture(event: Event) -> None:
            received.append(event)

        bus.subscribe("booking.status_changed", capture)

        crud = CrmCRUD(db_session, event_bus=bus)
        customer = await crud.create_customer(
            CustomerCreate(display_name="鈴木一郎"),
        )
        booking = await crud.create_booking(BookingCreate(
            customer_id=customer.id,
            service_name="美容施術",
            scheduled_at=datetime(2025, 6, 1, 10, 0, tzinfo=UTC),
        ))

        await crud.update_booking(
            booking.id,
            BookingUpdate(status="confirmed"),
        )

        assert len(received) == 1
        evt = received[0]
        assert evt.event_type == "booking.status_changed"
        assert evt.data["booking_id"] == booking.id
        assert evt.data["old_status"] == "inquiry"
        assert evt.data["new_status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_update_booking_no_event_if_status_unchanged(
        self, db_session: AsyncSession,
    ) -> None:
        """상태 변경 없이 다른 필드만 수정하면 이벤트가 발행되지 않는다."""
        bus = EventBus()
        received: list[Event] = []

        async def capture(event: Event) -> None:
            received.append(event)

        bus.subscribe("booking.status_changed", capture)

        crud = CrmCRUD(db_session, event_bus=bus)
        customer = await crud.create_customer(
            CustomerCreate(display_name="佐藤次郎"),
        )
        booking = await crud.create_booking(BookingCreate(
            customer_id=customer.id,
            service_name="整形相談",
            scheduled_at=datetime(2025, 7, 1, 14, 0, tzinfo=UTC),
        ))

        await crud.update_booking(
            booking.id,
            BookingUpdate(service_name="美容整形"),
        )

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_no_event_without_bus(
        self, db_session: AsyncSession,
    ) -> None:
        """EventBus 없이도 CRUD 동작은 정상."""
        crud = CrmCRUD(db_session)
        customer = await crud.create_customer(
            CustomerCreate(display_name="渡辺三郎"),
        )
        assert customer.id is not None


# ── 이벤트 발행 통합 테스트 (Content) ──────────────────────


class TestContentEventPublishing:
    """콘텐츠 서비스가 이벤트를 올바르게 발행하는지 검증."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_advance_pipeline_publishes_event(
        self, db_session: AsyncSession,
    ) -> None:
        """파이프라인 진행 시 content.pipeline.advanced 이벤트 발행."""
        bus = EventBus()
        received: list[Event] = []

        async def capture(event: Event) -> None:
            received.append(event)

        bus.subscribe("content.pipeline.advanced", capture)

        crud = ContentCRUD(db_session, event_bus=bus)
        content = await crud.create_content(
            ContentCreate(title="テスト動画", content_type="video", topic="大邱観光"),
        )
        assert content.pipeline_stage == "pending"

        # pending → script (AI handler) — mock Claude API
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(200, json={
                "content": [{"type": "text", "text": "台本テスト"}],
                "usage": {"input_tokens": 100, "output_tokens": 50},
            }),
        )
        config = {"anthropic_api_key": "sk-test-key"}
        result = await crud.advance_pipeline(content.id, config=config)

        assert result is not None
        assert result.pipeline_stage == "script"
        assert len(received) == 1
        evt = received[0]
        assert evt.event_type == "content.pipeline.advanced"
        assert evt.data["from_stage"] == "pending"
        assert evt.data["to_stage"] == "script"
        assert evt.source == "content_service"

    @pytest.mark.asyncio
    async def test_advance_non_ai_stage_publishes_event(
        self, db_session: AsyncSession,
    ) -> None:
        """AI 핸들러 없는 단계 진행에서도 이벤트가 발행된다."""
        bus = EventBus()
        received: list[Event] = []

        async def capture(event: Event) -> None:
            received.append(event)

        bus.subscribe("content.pipeline.advanced", capture)

        crud = ContentCRUD(db_session, event_bus=bus)
        content = await crud.create_content(
            ContentCreate(title="ブログ", content_type="blog", topic="美容"),
        )
        # 수동으로 image 단계 설정 (AI 핸들러 없는 단계)
        content.pipeline_stage = "image"
        await db_session.commit()
        await db_session.refresh(content)

        result = await crud.advance_pipeline(content.id)
        assert result is not None
        assert result.pipeline_stage == "voice"
        assert len(received) == 1
        assert received[0].data["from_stage"] == "image"
        assert received[0].data["to_stage"] == "voice"

    @pytest.mark.asyncio
    async def test_no_event_without_bus_content(
        self, db_session: AsyncSession,
    ) -> None:
        """EventBus 없이도 콘텐츠 CRUD 동작은 정상."""
        crud = ContentCRUD(db_session)
        content = await crud.create_content(
            ContentCreate(title="SNS投稿", content_type="sns", topic="観光"),
        )
        assert content.id is not None


# ── 이벤트 버스 구독 등록 검증 ─────────────────────────────


class TestEventSubscriptionWiring:
    """main.py lifespan에서 등록되는 이벤트 구독 구조 검증."""

    def test_handlers_are_async_callables(self) -> None:
        """핸들러들이 async callable이다."""
        import asyncio

        assert asyncio.iscoroutinefunction(_on_pipeline_advanced)
        assert asyncio.iscoroutinefunction(_on_customer_created)
        assert asyncio.iscoroutinefunction(_on_booking_status_changed)

    def test_bus_subscribe_and_verify(self) -> None:
        """EventBus에 핸들러 등록 후 get_handlers로 확인."""
        bus = EventBus()
        bus.subscribe("content.pipeline.advanced", _on_pipeline_advanced)
        bus.subscribe("customer.created", _on_customer_created)
        bus.subscribe(
            "booking.status_changed", _on_booking_status_changed,
        )

        assert len(bus.get_handlers("content.pipeline.advanced")) == 1
        assert len(bus.get_handlers("customer.created")) == 1
        assert len(bus.get_handlers("booking.status_changed")) == 1
