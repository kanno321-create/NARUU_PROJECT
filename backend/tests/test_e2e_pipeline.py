"""E2E 파이프라인 통합 테스트 — Phase 3 전체 흐름 검증."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import respx
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_core.event_bus import Event, EventBus
from naruu_core.plugins.content.schemas import ContentCreate
from naruu_core.plugins.content.service import ContentCRUD
from naruu_core.plugins.crm.schemas import (
    BookingCreate,
    BookingUpdate,
    CustomerCreate,
    InteractionCreate,
)
from naruu_core.plugins.crm.service import CrmCRUD

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MOCK_CONFIG = {"anthropic_api_key": "sk-test-e2e"}


# ── E2E: 콘텐츠 파이프라인 전체 흐름 ────────────────────


class TestContentPipelineE2E:
    """create → advance(script) → script 채움 → cost 기록 → 이벤트 발행."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_full_pipeline_flow(
        self, db_session: AsyncSession,
    ) -> None:
        """pending → script(단순) → image(AI) 전체 흐름 E2E."""
        events: list[Event] = []
        bus = EventBus()

        async def capture(event: Event) -> None:
            events.append(event)

        bus.subscribe("content.pipeline.advanced", capture)

        crud = ContentCRUD(db_session, event_bus=bus)

        # 1. 콘텐츠 생성
        content = await crud.create_content(
            ContentCreate(
                title="大邱医療観光ガイド",
                content_type="video",
                topic="大邱の美容クリニック紹介",
            ),
        )
        assert content.pipeline_stage == "pending"
        assert content.cost_usd == 0.0

        # 2. pending → script (핸들러 없음, 단순 진행)
        result = await crud.advance_pipeline(content.id)
        assert result is not None
        assert result.pipeline_stage == "script"
        assert len(events) == 1

        # 3. script → image (AI ScriptGenerator 실행)
        respx.post(CLAUDE_API_URL).mock(
            return_value=Response(200, json={
                "content": [{"type": "text", "text": "大邱美容台本"}],
                "usage": {"input_tokens": 200, "output_tokens": 150},
            }),
        )
        result = await crud.advance_pipeline(content.id, config=MOCK_CONFIG)

        # 4. 검증: script 채워짐 + image 단계
        assert result is not None
        assert result.pipeline_stage == "image"
        assert result.script == "大邱美容台本"

        # 5. 검증: cost 기록됨
        assert result.cost_usd > 0.0

        # 6. 검증: 이벤트 2건 (pending→script, script→image)
        assert len(events) == 2
        assert events[1].data["from_stage"] == "script"
        assert events[1].data["to_stage"] == "image"
        assert events[1].data["cost_usd"] > 0.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_pipeline_failure_records_error(
        self, db_session: AsyncSession,
    ) -> None:
        """AI 호출 실패 시 failed 상태 + 에러 메시지 기록."""
        bus = EventBus()
        events: list[Event] = []

        async def capture(event: Event) -> None:
            events.append(event)

        bus.subscribe("content.pipeline.advanced", capture)

        crud = ContentCRUD(db_session, event_bus=bus)
        content = await crud.create_content(
            ContentCreate(
                title="失敗テスト",
                content_type="blog",
                topic="テスト",
            ),
        )

        # pending → script (단순 진행)
        await crud.advance_pipeline(content.id)

        # script 단계에서 API 401 에러
        respx.post(CLAUDE_API_URL).mock(
            return_value=Response(401, json={"error": "unauthorized"}),
        )
        result = await crud.advance_pipeline(content.id, config=MOCK_CONFIG)

        assert result is not None
        assert result.pipeline_stage == "failed"
        assert result.error_message is not None

        # 이벤트 2건: pending→script, script→failed
        assert len(events) == 2
        assert events[1].data["to_stage"] == "failed"


# ── E2E: LINE → CRM 통합 흐름 ─────────────────────────


class TestLineCrmE2E:
    """Customer 생성 → Interaction 기록 → AI 응답 생성 → 이벤트."""

    @pytest.mark.asyncio
    async def test_customer_lifecycle(
        self, db_session: AsyncSession,
    ) -> None:
        """고객 생성 → 예약 → 상태 변경 → 이벤트 체인 E2E."""
        events: list[Event] = []
        bus = EventBus()

        async def capture(event: Event) -> None:
            events.append(event)

        bus.subscribe("customer.created", capture)
        bus.subscribe("booking.status_changed", capture)

        crud = CrmCRUD(db_session, event_bus=bus)

        # 1. 고객 생성
        customer = await crud.create_customer(
            CustomerCreate(
                display_name="山田花子",
                line_user_id="U_yamada_123",
                language="ja",
            ),
        )
        assert customer.id is not None

        # 2. 고객 생성 이벤트 확인
        assert len(events) == 1
        assert events[0].event_type == "customer.created"
        assert events[0].data["display_name"] == "山田花子"

        # 3. Interaction 기록
        interaction = await crud.create_interaction(
            InteractionCreate(
                customer_id=customer.id,
                channel="line",
                direction="inbound",
                content="美容整形について教えてください",
            ),
        )
        assert interaction.id is not None

        # 4. 예약 생성
        booking = await crud.create_booking(
            BookingCreate(
                customer_id=customer.id,
                service_name="美容カウンセリング",
                scheduled_at=datetime(2025, 8, 1, 10, 0, tzinfo=UTC),
            ),
        )
        assert booking.status == "inquiry"

        # 5. 예약 상태 변경 → 이벤트
        updated = await crud.update_booking(
            booking.id,
            BookingUpdate(status="confirmed"),
        )
        assert updated is not None
        assert updated.status == "confirmed"

        # 6. booking.status_changed 이벤트 확인
        assert len(events) == 2
        booking_evt = events[1]
        assert booking_evt.event_type == "booking.status_changed"
        assert booking_evt.data["old_status"] == "inquiry"
        assert booking_evt.data["new_status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_booking_completed_event_chain(
        self, db_session: AsyncSession,
    ) -> None:
        """예약 confirmed → completed 전체 체인."""
        events: list[Event] = []
        bus = EventBus()

        async def capture(event: Event) -> None:
            events.append(event)

        bus.subscribe("booking.status_changed", capture)

        crud = CrmCRUD(db_session, event_bus=bus)
        customer = await crud.create_customer(
            CustomerCreate(display_name="佐藤太郎"),
        )
        booking = await crud.create_booking(
            BookingCreate(
                customer_id=customer.id,
                service_name="整形手術",
                scheduled_at=datetime(2025, 9, 15, 9, 0, tzinfo=UTC),
            ),
        )

        # inquiry → confirmed
        await crud.update_booking(
            booking.id, BookingUpdate(status="confirmed"),
        )
        # confirmed → completed
        await crud.update_booking(
            booking.id, BookingUpdate(status="completed"),
        )

        assert len(events) == 2
        assert events[0].data["old_status"] == "inquiry"
        assert events[0].data["new_status"] == "confirmed"
        assert events[1].data["old_status"] == "confirmed"
        assert events[1].data["new_status"] == "completed"
