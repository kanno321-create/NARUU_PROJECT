"""CRM + LINE 연동 테스트."""

from __future__ import annotations

import hashlib
import hmac
from base64 import b64encode

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from naruu_core.models.customer import Customer
from naruu_core.plugins.crm.line_client import LineClient
from naruu_core.plugins.crm.plugin import Plugin as CrmPlugin
from naruu_core.plugins.crm.schemas import (
    BookingCreate,
    BookingUpdate,
    CustomerCreate,
    CustomerUpdate,
    InteractionCreate,
)
from naruu_core.plugins.crm.service import CrmCRUD

# ── Unit 테스트: CRM 스키마 ──


@pytest.mark.unit
class TestCrmSchemas:
    """CRM 스키마 유효성 테스트."""

    def test_customer_create_valid(self) -> None:
        """유효한 고객 생성."""
        data = CustomerCreate(
            display_name="田中太郎", language="ja", line_user_id="U123"
        )
        assert data.display_name == "田中太郎"
        assert data.language == "ja"

    def test_customer_create_invalid_language(self) -> None:
        """유효하지 않은 언어 코드."""
        with pytest.raises(ValidationError):
            CustomerCreate(display_name="Test", language="zh")

    def test_booking_create_valid(self) -> None:
        """유효한 예약 생성."""
        data = BookingCreate(
            customer_id="cust-1",
            partner_id="part-1",
            service_name="二重整形",
            price_krw=1500000,
        )
        assert data.price_krw == 1500000

    def test_booking_update_status_valid(self) -> None:
        """유효한 예약 상태."""
        for s in ("inquiry", "confirmed", "completed", "cancelled"):
            data = BookingUpdate(status=s)
            assert data.status == s

    def test_booking_update_status_invalid(self) -> None:
        """유효하지 않은 예약 상태."""
        with pytest.raises(ValidationError):
            BookingUpdate(status="unknown")

    def test_interaction_create_valid(self) -> None:
        """유효한 상호작용 기록."""
        data = InteractionCreate(
            customer_id="c-1", channel="line", direction="inbound", content="hello"
        )
        assert data.channel == "line"
        assert data.direction == "inbound"


# ── Unit 테스트: LINE 서명 검증 ──


@pytest.mark.unit
class TestLineSignature:
    """LINE 웹훅 서명 검증 테스트."""

    def test_valid_signature(self) -> None:
        """올바른 서명 검증 성공."""
        secret = "test-channel-secret"
        body = b'{"events":[]}'
        digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
        signature = b64encode(digest).decode()

        client = LineClient(
            channel_secret=secret,
            channel_access_token="test-token",
        )
        assert client.verify_signature(body, signature) is True

    def test_invalid_signature(self) -> None:
        """잘못된 서명 검증 실패."""
        client = LineClient(
            channel_secret="secret",
            channel_access_token="token",
        )
        assert client.verify_signature(b"body", "wrong-sig") is False

    def test_empty_credentials_raises(self) -> None:
        """빈 자격증명은 ValueError."""
        with pytest.raises(ValueError):
            LineClient(channel_secret="", channel_access_token="token")

    def test_text_message_helper(self) -> None:
        """텍스트 메시지 헬퍼."""
        msg = LineClient.text_message("こんにちは")
        assert msg == {"type": "text", "text": "こんにちは"}


# ── Unit 테스트: CRM 플러그인 ──


@pytest.mark.unit
class TestCrmPlugin:
    """CRM 플러그인 인터페이스 테스트."""

    def test_plugin_name(self) -> None:
        plugin = CrmPlugin()
        assert plugin.name == "crm"

    def test_plugin_capabilities(self) -> None:
        plugin = CrmPlugin()
        caps = plugin.capabilities()
        assert "customer.create" in caps
        assert "booking.list" in caps
        assert "line.send" in caps
        assert len(caps) == 12

    async def test_plugin_execute(self) -> None:
        plugin = CrmPlugin()
        await plugin.initialize({})
        result = await plugin.execute("customer.list", {})
        assert result["status"] == "ok"


# ── Integration 테스트: Customer CRUD ──


@pytest.mark.integration
class TestCustomerCRUD:
    """고객 CRUD 통합 테스트."""

    async def test_create_customer(self, db_session: AsyncSession) -> None:
        """고객 생성."""
        crud = CrmCRUD(db_session)
        customer = await crud.create_customer(
            CustomerCreate(
                display_name="田中太郎",
                line_user_id="U1234567890",
                language="ja",
            )
        )
        assert customer.id is not None
        assert customer.display_name == "田中太郎"
        assert customer.line_user_id == "U1234567890"

    async def test_get_customer_by_line_id(self, db_session: AsyncSession) -> None:
        """LINE ID로 고객 조회."""
        crud = CrmCRUD(db_session)
        await crud.create_customer(
            CustomerCreate(display_name="Taro", line_user_id="U999")
        )
        found = await crud.get_customer_by_line_id("U999")
        assert found is not None
        assert found.display_name == "Taro"

    async def test_get_nonexistent_customer(self, db_session: AsyncSession) -> None:
        """존재하지 않는 고객 → None."""
        crud = CrmCRUD(db_session)
        assert await crud.get_customer("nope") is None

    async def test_list_customers(self, db_session: AsyncSession) -> None:
        """고객 목록 조회."""
        crud = CrmCRUD(db_session)
        await crud.create_customer(CustomerCreate(display_name="A"))
        await crud.create_customer(CustomerCreate(display_name="B"))
        customers = await crud.list_customers()
        assert len(customers) == 2

    async def test_update_customer(self, db_session: AsyncSession) -> None:
        """고객 수정."""
        crud = CrmCRUD(db_session)
        c = await crud.create_customer(CustomerCreate(display_name="Old"))
        updated = await crud.update_customer(
            c.id, CustomerUpdate(display_name="New", language="ko")
        )
        assert updated is not None
        assert updated.display_name == "New"
        assert updated.language == "ko"


# ── Integration 테스트: Booking CRUD ──


@pytest.mark.integration
class TestBookingCRUD:
    """예약 CRUD 통합 테스트."""

    async def _make_customer(self, session: AsyncSession) -> Customer:
        crud = CrmCRUD(session)
        return await crud.create_customer(
            CustomerCreate(display_name="Guest")
        )

    async def test_create_booking(self, db_session: AsyncSession) -> None:
        """예약 생성."""
        customer = await self._make_customer(db_session)
        crud = CrmCRUD(db_session)
        booking = await crud.create_booking(
            BookingCreate(
                customer_id=customer.id,
                service_name="二重整形",
                price_krw=1500000,
                commission_krw=300000,
            )
        )
        assert booking.status == "inquiry"
        assert booking.price_krw == 1500000

    async def test_booking_status_transition(self, db_session: AsyncSession) -> None:
        """예약 상태 전환: inquiry → confirmed → completed."""
        customer = await self._make_customer(db_session)
        crud = CrmCRUD(db_session)
        booking = await crud.create_booking(
            BookingCreate(customer_id=customer.id)
        )
        assert booking.status == "inquiry"

        updated = await crud.update_booking(
            booking.id, BookingUpdate(status="confirmed")
        )
        assert updated is not None
        assert updated.status == "confirmed"

        completed = await crud.update_booking(
            booking.id, BookingUpdate(status="completed")
        )
        assert completed is not None
        assert completed.status == "completed"

    async def test_list_bookings_by_customer(self, db_session: AsyncSession) -> None:
        """고객별 예약 목록."""
        c1 = await self._make_customer(db_session)
        crud = CrmCRUD(db_session)
        await crud.create_booking(BookingCreate(customer_id=c1.id))
        await crud.create_booking(BookingCreate(customer_id=c1.id))
        bookings = await crud.list_bookings(customer_id=c1.id)
        assert len(bookings) == 2

    async def test_list_bookings_by_status(self, db_session: AsyncSession) -> None:
        """상태별 예약 목록."""
        customer = await self._make_customer(db_session)
        crud = CrmCRUD(db_session)
        b = await crud.create_booking(BookingCreate(customer_id=customer.id))
        await crud.update_booking(b.id, BookingUpdate(status="confirmed"))
        await crud.create_booking(BookingCreate(customer_id=customer.id))

        confirmed = await crud.list_bookings(status="confirmed")
        assert len(confirmed) == 1
        inquiry = await crud.list_bookings(status="inquiry")
        assert len(inquiry) == 1

    async def test_update_nonexistent_booking(self, db_session: AsyncSession) -> None:
        """존재하지 않는 예약 수정 → None."""
        crud = CrmCRUD(db_session)
        assert await crud.update_booking("nope", BookingUpdate(status="confirmed")) is None


# ── Integration 테스트: Interaction ──


@pytest.mark.integration
class TestInteractionCRUD:
    """상호작용 CRUD 통합 테스트."""

    async def test_create_interaction(self, db_session: AsyncSession) -> None:
        """상호작용 기록."""
        crud = CrmCRUD(db_session)
        customer = await crud.create_customer(
            CustomerCreate(display_name="Guest")
        )
        interaction = await crud.create_interaction(
            InteractionCreate(
                customer_id=customer.id,
                channel="line",
                direction="inbound",
                content="こんにちは",
            )
        )
        assert interaction.channel == "line"
        assert interaction.content == "こんにちは"

    async def test_list_interactions(self, db_session: AsyncSession) -> None:
        """고객 상호작용 목록."""
        crud = CrmCRUD(db_session)
        customer = await crud.create_customer(
            CustomerCreate(display_name="Guest")
        )
        await crud.create_interaction(
            InteractionCreate(
                customer_id=customer.id,
                channel="line",
                direction="inbound",
                content="msg1",
            )
        )
        await crud.create_interaction(
            InteractionCreate(
                customer_id=customer.id,
                channel="phone",
                direction="outbound",
                content="called",
            )
        )
        all_items = await crud.list_interactions(customer.id)
        assert len(all_items) == 2

        line_only = await crud.list_interactions(customer.id, channel="line")
        assert len(line_only) == 1


# ── Integration 테스트: LINE 웹훅 ──


@pytest.mark.integration
class TestLineWebhook:
    """LINE 웹훅 처리 테스트."""

    async def test_webhook_empty_events(self) -> None:
        """빈 이벤트 목록 처리."""
        from naruu_api.routes.line_webhook import _handle_event
        # 빈 유저 → 무시
        await _handle_event({"type": "message", "source": {}})

    async def test_webhook_follow_event(self) -> None:
        """follow 이벤트 처리."""
        from naruu_api.routes.line_webhook import _handle_event

        await _handle_event({
            "type": "follow",
            "source": {"type": "user", "userId": "U_test_follow"},
        })
        # 에러 없이 처리되면 성공

    async def test_webhook_message_event(self) -> None:
        """message 이벤트 처리 (LINE 미연결 상태)."""
        from naruu_api.routes.line_webhook import _handle_event

        await _handle_event({
            "type": "message",
            "source": {"type": "user", "userId": "U_test_msg"},
            "replyToken": "test-reply-token",
            "message": {"type": "text", "text": "テスト"},
        })


# ── Smoke 테스트 ──


@pytest.mark.smoke
class TestCrmSmoke:
    """CRM 스모크 테스트."""

    async def test_customers_table_exists(self, db_engine: AsyncEngine) -> None:
        """customers 테이블 존재."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='customers'"
                )
            )
            assert result.scalar() == "customers"

    async def test_bookings_table_exists(self, db_engine: AsyncEngine) -> None:
        """bookings 테이블 존재."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='bookings'"
                )
            )
            assert result.scalar() == "bookings"

    async def test_interactions_table_exists(self, db_engine: AsyncEngine) -> None:
        """interactions 테이블 존재."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='interactions'"
                )
            )
            assert result.scalar() == "interactions"
