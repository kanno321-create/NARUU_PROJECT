"""거래처 관리 테스트."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from naruu_core.plugins.partner.plugin import Plugin as PartnerPlugin
from naruu_core.plugins.partner.schemas import (
    PartnerCreate,
    PartnerUpdate,
    ServiceCreate,
    ServiceUpdate,
)
from naruu_core.plugins.partner.service import PartnerCRUD

# ── Unit 테스트: 스키마 검증 ──


@pytest.mark.unit
class TestPartnerSchemas:
    """스키마 유효성 검증 테스트."""

    def test_partner_create_valid(self) -> None:
        """유효한 거래처 생성 데이터."""
        data = PartnerCreate(name_ja="東京クリニック", category="medical")
        assert data.name_ja == "東京クリニック"
        assert data.category == "medical"
        assert data.commission_rate == Decimal("20.00")

    def test_partner_create_invalid_category(self) -> None:
        """유효하지 않은 카테고리."""
        with pytest.raises(ValidationError):
            PartnerCreate(name_ja="Test", category="invalid")

    def test_partner_update_partial(self) -> None:
        """부분 업데이트 스키마."""
        data = PartnerUpdate(name_ko="도쿄클리닉")
        dumped = data.model_dump(exclude_unset=True)
        assert dumped == {"name_ko": "도쿄클리닉"}

    def test_service_create_valid(self) -> None:
        """유효한 서비스 생성 데이터."""
        data = ServiceCreate(name_ja="二重整形", price_krw=1500000, duration_minutes=90)
        assert data.price_krw == 1500000
        assert data.duration_minutes == 90

    def test_service_create_invalid_price(self) -> None:
        """음수 가격 불허."""
        with pytest.raises(ValidationError):
            ServiceCreate(name_ja="Test", price_krw=-100, duration_minutes=60)

    def test_service_create_invalid_duration(self) -> None:
        """0분 이하 또는 1440분 초과 불허."""
        with pytest.raises(ValidationError):
            ServiceCreate(name_ja="Test", price_krw=100, duration_minutes=0)


# ── Unit 테스트: 플러그인 ──


@pytest.mark.unit
class TestPartnerPlugin:
    """플러그인 인터페이스 테스트."""

    def test_plugin_name(self) -> None:
        """플러그인 이름."""
        plugin = PartnerPlugin()
        assert plugin.name == "partner"

    def test_plugin_capabilities(self) -> None:
        """플러그인 지원 명령."""
        plugin = PartnerPlugin()
        caps = plugin.capabilities()
        assert "partner.create" in caps
        assert "service.list" in caps
        assert len(caps) == 10

    async def test_plugin_execute(self) -> None:
        """플러그인 execute는 상태 ok 반환."""
        plugin = PartnerPlugin()
        await plugin.initialize({})
        result = await plugin.execute("partner.list", {})
        assert result["status"] == "ok"
        assert result["plugin"] == "partner"


# ── Integration 테스트: Partner CRUD ──


@pytest.mark.integration
class TestPartnerCRUD:
    """거래처 CRUD 통합 테스트."""

    async def test_create_partner(self, db_session: AsyncSession) -> None:
        """거래처 생성."""
        crud = PartnerCRUD(db_session)
        partner = await crud.create_partner(
            PartnerCreate(name_ja="大邱美容クリニック", category="beauty")
        )
        assert partner.id is not None
        assert partner.name_ja == "大邱美容クリニック"
        assert partner.category == "beauty"
        assert partner.commission_rate == Decimal("20.00")
        assert partner.is_active is True

    async def test_get_partner(self, db_session: AsyncSession) -> None:
        """거래처 조회."""
        crud = PartnerCRUD(db_session)
        created = await crud.create_partner(
            PartnerCreate(name_ja="テストクリニック", category="medical")
        )
        fetched = await crud.get_partner(created.id)
        assert fetched is not None
        assert fetched.name_ja == "テストクリニック"

    async def test_get_nonexistent_partner(self, db_session: AsyncSession) -> None:
        """존재하지 않는 거래처 조회 → None."""
        crud = PartnerCRUD(db_session)
        result = await crud.get_partner("nonexistent-id")
        assert result is None

    async def test_list_partners_filter_category(self, db_session: AsyncSession) -> None:
        """카테고리별 필터 조회."""
        crud = PartnerCRUD(db_session)
        await crud.create_partner(PartnerCreate(name_ja="Medical A", category="medical"))
        await crud.create_partner(PartnerCreate(name_ja="Beauty B", category="beauty"))
        await crud.create_partner(PartnerCreate(name_ja="Medical C", category="medical"))

        medical = await crud.list_partners(category="medical")
        assert len(medical) == 2
        beauty = await crud.list_partners(category="beauty")
        assert len(beauty) == 1

    async def test_update_partner(self, db_session: AsyncSession) -> None:
        """거래처 수정."""
        crud = PartnerCRUD(db_session)
        partner = await crud.create_partner(
            PartnerCreate(name_ja="Original", category="tourism")
        )
        updated = await crud.update_partner(
            partner.id,
            PartnerUpdate(name_ko="오리지널", commission_rate=Decimal("15.00")),
        )
        assert updated is not None
        assert updated.name_ko == "오리지널"
        assert updated.commission_rate == Decimal("15.00")

    async def test_update_nonexistent_partner(self, db_session: AsyncSession) -> None:
        """존재하지 않는 거래처 수정 → None."""
        crud = PartnerCRUD(db_session)
        result = await crud.update_partner("nope", PartnerUpdate(name_ko="test"))
        assert result is None

    async def test_delete_partner(self, db_session: AsyncSession) -> None:
        """거래처 삭제."""
        crud = PartnerCRUD(db_session)
        partner = await crud.create_partner(
            PartnerCreate(name_ja="To Delete", category="medical")
        )
        deleted = await crud.delete_partner(partner.id)
        assert deleted is True
        assert await crud.get_partner(partner.id) is None

    async def test_delete_nonexistent(self, db_session: AsyncSession) -> None:
        """존재하지 않는 거래처 삭제 → False."""
        crud = PartnerCRUD(db_session)
        assert await crud.delete_partner("nope") is False


# ── Integration 테스트: Service CRUD ──


@pytest.mark.integration
class TestServiceCRUD:
    """서비스 CRUD 통합 테스트."""

    async def test_create_service(self, db_session: AsyncSession) -> None:
        """서비스 생성."""
        crud = PartnerCRUD(db_session)
        partner = await crud.create_partner(
            PartnerCreate(name_ja="Clinic", category="medical")
        )
        service = await crud.create_service(
            partner.id,
            ServiceCreate(name_ja="二重整形", price_krw=1500000, duration_minutes=90),
        )
        assert service is not None
        assert service.partner_id == partner.id
        assert service.price_krw == 1500000

    async def test_create_service_invalid_partner(self, db_session: AsyncSession) -> None:
        """존재하지 않는 거래처에 서비스 생성 → None."""
        crud = PartnerCRUD(db_session)
        result = await crud.create_service(
            "nonexistent",
            ServiceCreate(name_ja="Test", price_krw=100, duration_minutes=30),
        )
        assert result is None

    async def test_list_services(self, db_session: AsyncSession) -> None:
        """서비스 목록 조회."""
        crud = PartnerCRUD(db_session)
        partner = await crud.create_partner(
            PartnerCreate(name_ja="Clinic", category="beauty")
        )
        await crud.create_service(
            partner.id,
            ServiceCreate(name_ja="Service A", price_krw=100000, duration_minutes=30),
        )
        await crud.create_service(
            partner.id,
            ServiceCreate(name_ja="Service B", price_krw=200000, duration_minutes=60),
        )
        services = await crud.list_services(partner.id)
        assert len(services) == 2

    async def test_update_service(self, db_session: AsyncSession) -> None:
        """서비스 수정."""
        crud = PartnerCRUD(db_session)
        partner = await crud.create_partner(
            PartnerCreate(name_ja="Clinic", category="medical")
        )
        service = await crud.create_service(
            partner.id,
            ServiceCreate(name_ja="Original", price_krw=100000, duration_minutes=30),
        )
        assert service is not None
        updated = await crud.update_service(
            service.id, ServiceUpdate(price_krw=150000)
        )
        assert updated is not None
        assert updated.price_krw == 150000

    async def test_delete_service(self, db_session: AsyncSession) -> None:
        """서비스 삭제."""
        crud = PartnerCRUD(db_session)
        partner = await crud.create_partner(
            PartnerCreate(name_ja="Clinic", category="tourism")
        )
        service = await crud.create_service(
            partner.id,
            ServiceCreate(name_ja="Tour", price_krw=50000, duration_minutes=120),
        )
        assert service is not None
        deleted = await crud.delete_service(service.id)
        assert deleted is True


# ── Smoke 테스트 ──


@pytest.mark.smoke
class TestPartnerSmoke:
    """거래처 시스템 스모크 테스트."""

    async def test_partners_table_exists(self, db_engine: AsyncEngine) -> None:
        """partners 테이블이 존재한다."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='partners'")
            )
            assert result.scalar() == "partners"

    async def test_partner_services_table_exists(self, db_engine: AsyncEngine) -> None:
        """partner_services 테이블이 존재한다."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='partner_services'"
                )
            )
            assert result.scalar() == "partner_services"
