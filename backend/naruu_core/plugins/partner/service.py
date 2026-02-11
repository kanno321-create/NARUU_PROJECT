"""거래처 CRUD 서비스."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_core.models.partner import Partner, PartnerService
from naruu_core.plugins.partner.schemas import (
    PartnerCreate,
    PartnerUpdate,
    ServiceCreate,
    ServiceUpdate,
)


class PartnerCRUD:
    """거래처 CRUD 오퍼레이션."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- Partner --

    async def create_partner(self, data: PartnerCreate) -> Partner:
        """거래처 생성."""
        partner = Partner(
            name_ja=data.name_ja,
            name_ko=data.name_ko,
            category=data.category,
            address=data.address,
            phone=data.phone,
            commission_rate=data.commission_rate,
            notes=data.notes,
        )
        self._session.add(partner)
        await self._session.commit()
        await self._session.refresh(partner)
        return partner

    async def get_partner(self, partner_id: str) -> Partner | None:
        """거래처 단건 조회."""
        result = await self._session.execute(
            select(Partner).where(Partner.id == partner_id)
        )
        return result.scalar_one_or_none()

    async def list_partners(
        self,
        category: str | None = None,
        active_only: bool = True,
    ) -> list[Partner]:
        """거래처 목록 조회."""
        stmt = select(Partner)
        if category:
            stmt = stmt.where(Partner.category == category)
        if active_only:
            stmt = stmt.where(Partner.is_active.is_(True))
        stmt = stmt.order_by(Partner.name_ja)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_partner(self, partner_id: str, data: PartnerUpdate) -> Partner | None:
        """거래처 수정."""
        partner = await self.get_partner(partner_id)
        if partner is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(partner, field, value)
        await self._session.commit()
        await self._session.refresh(partner)
        return partner

    async def delete_partner(self, partner_id: str) -> bool:
        """거래처 삭제."""
        partner = await self.get_partner(partner_id)
        if partner is None:
            return False
        await self._session.delete(partner)
        await self._session.commit()
        return True

    # -- Service --

    async def create_service(self, partner_id: str, data: ServiceCreate) -> PartnerService | None:
        """서비스 생성."""
        partner = await self.get_partner(partner_id)
        if partner is None:
            return None
        service = PartnerService(
            partner_id=partner_id,
            name_ja=data.name_ja,
            name_ko=data.name_ko,
            price_krw=data.price_krw,
            duration_minutes=data.duration_minutes,
            description=data.description,
        )
        self._session.add(service)
        await self._session.commit()
        await self._session.refresh(service)
        return service

    async def get_service(self, service_id: str) -> PartnerService | None:
        """서비스 단건 조회."""
        result = await self._session.execute(
            select(PartnerService).where(PartnerService.id == service_id)
        )
        return result.scalar_one_or_none()

    async def list_services(self, partner_id: str) -> list[PartnerService]:
        """특정 거래처의 서비스 목록."""
        stmt = (
            select(PartnerService)
            .where(PartnerService.partner_id == partner_id)
            .where(PartnerService.is_active.is_(True))
            .order_by(PartnerService.name_ja)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_service(self, service_id: str, data: ServiceUpdate) -> PartnerService | None:
        """서비스 수정."""
        service = await self.get_service(service_id)
        if service is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(service, field, value)
        await self._session.commit()
        await self._session.refresh(service)
        return service

    async def delete_service(self, service_id: str) -> bool:
        """서비스 삭제."""
        service = await self.get_service(service_id)
        if service is None:
            return False
        await self._session.delete(service)
        await self._session.commit()
        return True
