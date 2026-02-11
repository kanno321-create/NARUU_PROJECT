"""CRM CRUD 서비스."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_core.event_bus import Event, EventBus
from naruu_core.models.customer import Booking, Customer, Interaction
from naruu_core.plugins.crm.schemas import (
    BookingCreate,
    BookingUpdate,
    CustomerCreate,
    CustomerUpdate,
    InteractionCreate,
)


class CrmCRUD:
    """CRM CRUD 오퍼레이션."""

    def __init__(
        self,
        session: AsyncSession,
        event_bus: EventBus | None = None,
    ) -> None:
        self._session = session
        self._event_bus = event_bus

    # -- Customer --

    async def create_customer(self, data: CustomerCreate) -> Customer:
        """고객 생성."""
        customer = Customer(
            line_user_id=data.line_user_id,
            display_name=data.display_name,
            language=data.language,
            phone=data.phone,
            email=data.email,
            notes=data.notes,
        )
        self._session.add(customer)
        await self._session.commit()
        await self._session.refresh(customer)

        if self._event_bus is not None:
            await self._event_bus.publish(Event(
                event_type="customer.created",
                data={
                    "customer_id": customer.id,
                    "line_user_id": customer.line_user_id or "",
                    "display_name": customer.display_name,
                },
                source="crm_service",
            ))

        return customer

    async def get_customer(self, customer_id: str) -> Customer | None:
        """고객 단건 조회."""
        result = await self._session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()

    async def get_customer_by_line_id(self, line_user_id: str) -> Customer | None:
        """LINE user ID로 고객 조회."""
        result = await self._session.execute(
            select(Customer).where(Customer.line_user_id == line_user_id)
        )
        return result.scalar_one_or_none()

    async def list_customers(
        self,
        status: str | None = None,
    ) -> list[Customer]:
        """고객 목록 조회."""
        stmt = select(Customer).order_by(Customer.display_name)
        if status:
            stmt = stmt.where(Customer.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_customer(
        self, customer_id: str, data: CustomerUpdate
    ) -> Customer | None:
        """고객 수정."""
        customer = await self.get_customer(customer_id)
        if customer is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        await self._session.commit()
        await self._session.refresh(customer)
        return customer

    # -- Booking --

    async def create_booking(self, data: BookingCreate) -> Booking:
        """예약 생성."""
        booking = Booking(
            customer_id=data.customer_id,
            partner_id=data.partner_id,
            service_name=data.service_name,
            price_krw=data.price_krw,
            commission_krw=data.commission_krw,
            scheduled_at=data.scheduled_at,
            notes=data.notes,
        )
        self._session.add(booking)
        await self._session.commit()
        await self._session.refresh(booking)
        return booking

    async def get_booking(self, booking_id: str) -> Booking | None:
        """예약 단건 조회."""
        result = await self._session.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def list_bookings(
        self,
        customer_id: str | None = None,
        status: str | None = None,
    ) -> list[Booking]:
        """예약 목록 조회."""
        stmt = select(Booking).order_by(Booking.created_at.desc())
        if customer_id:
            stmt = stmt.where(Booking.customer_id == customer_id)
        if status:
            stmt = stmt.where(Booking.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_booking(
        self, booking_id: str, data: BookingUpdate
    ) -> Booking | None:
        """예약 수정 (상태 전환 포함)."""
        booking = await self.get_booking(booking_id)
        if booking is None:
            return None
        old_status = booking.status
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(booking, field, value)
        await self._session.commit()
        await self._session.refresh(booking)

        if (
            self._event_bus is not None
            and old_status != booking.status
        ):
            await self._event_bus.publish(Event(
                event_type="booking.status_changed",
                data={
                    "booking_id": booking.id,
                    "customer_id": booking.customer_id,
                    "old_status": old_status,
                    "new_status": booking.status,
                },
                source="crm_service",
            ))

        return booking

    # -- Interaction --

    async def create_interaction(self, data: InteractionCreate) -> Interaction:
        """상호작용 기록."""
        interaction = Interaction(
            customer_id=data.customer_id,
            channel=data.channel,
            direction=data.direction,
            content=data.content,
            metadata_json=data.metadata_json,
        )
        self._session.add(interaction)
        await self._session.commit()
        await self._session.refresh(interaction)
        return interaction

    async def list_interactions(
        self,
        customer_id: str,
        channel: str | None = None,
    ) -> list[Interaction]:
        """고객 상호작용 목록."""
        stmt = (
            select(Interaction)
            .where(Interaction.customer_id == customer_id)
            .order_by(Interaction.created_at.desc())
        )
        if channel:
            stmt = stmt.where(Interaction.channel == channel)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
