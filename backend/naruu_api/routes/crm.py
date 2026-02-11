"""CRM 라우터 — 고객/예약/상호작용 CRUD REST API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_api.deps import get_db_session
from naruu_core.auth.middleware import get_current_user
from naruu_core.plugins.crm.schemas import (
    BookingCreate,
    BookingResponse,
    BookingUpdate,
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
    InteractionCreate,
    InteractionResponse,
)
from naruu_core.plugins.crm.service import CrmCRUD

router = APIRouter(prefix="/crm", tags=["crm"])


def _customer_resp(c: object) -> CustomerResponse:
    return CustomerResponse(
        id=c.id,  # type: ignore[attr-defined]
        line_user_id=c.line_user_id,  # type: ignore[attr-defined]
        display_name=c.display_name,  # type: ignore[attr-defined]
        language=c.language,  # type: ignore[attr-defined]
        phone=c.phone,  # type: ignore[attr-defined]
        email=c.email,  # type: ignore[attr-defined]
        status=c.status,  # type: ignore[attr-defined]
        notes=c.notes,  # type: ignore[attr-defined]
    )


def _booking_resp(b: object) -> BookingResponse:
    return BookingResponse(
        id=b.id,  # type: ignore[attr-defined]
        customer_id=b.customer_id,  # type: ignore[attr-defined]
        partner_id=b.partner_id,  # type: ignore[attr-defined]
        service_name=b.service_name,  # type: ignore[attr-defined]
        status=b.status,  # type: ignore[attr-defined]
        price_krw=b.price_krw,  # type: ignore[attr-defined]
        commission_krw=b.commission_krw,  # type: ignore[attr-defined]
        scheduled_at=b.scheduled_at,  # type: ignore[attr-defined]
        notes=b.notes,  # type: ignore[attr-defined]
    )


def _interaction_resp(i: object) -> InteractionResponse:
    return InteractionResponse(
        id=i.id,  # type: ignore[attr-defined]
        customer_id=i.customer_id,  # type: ignore[attr-defined]
        channel=i.channel,  # type: ignore[attr-defined]
        direction=i.direction,  # type: ignore[attr-defined]
        content=i.content,  # type: ignore[attr-defined]
        metadata_json=i.metadata_json,  # type: ignore[attr-defined]
    )


# -- Customer --


@router.post("/customers", response_model=CustomerResponse, status_code=201)
async def create_customer(
    req: CustomerCreate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CustomerResponse:
    """고객 등록."""
    crud = CrmCRUD(session)
    customer = await crud.create_customer(req)
    return _customer_resp(customer)


@router.get("/customers", response_model=list[CustomerResponse])
async def list_customers(
    status_filter: str | None = None,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[CustomerResponse]:
    """고객 목록 조회."""
    crud = CrmCRUD(session)
    customers = await crud.list_customers(status=status_filter)
    return [_customer_resp(c) for c in customers]


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CustomerResponse:
    """고객 상세 조회."""
    crud = CrmCRUD(session)
    customer = await crud.get_customer(customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )
    return _customer_resp(customer)


@router.patch("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    req: CustomerUpdate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CustomerResponse:
    """고객 수정."""
    crud = CrmCRUD(session)
    customer = await crud.update_customer(customer_id, req)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )
    return _customer_resp(customer)


# -- Booking --


@router.post("/bookings", response_model=BookingResponse, status_code=201)
async def create_booking(
    req: BookingCreate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> BookingResponse:
    """예약 생성."""
    crud = CrmCRUD(session)
    booking = await crud.create_booking(req)
    return _booking_resp(booking)


@router.get("/bookings", response_model=list[BookingResponse])
async def list_bookings(
    customer_id: str | None = None,
    status_filter: str | None = None,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[BookingResponse]:
    """예약 목록 조회."""
    crud = CrmCRUD(session)
    bookings = await crud.list_bookings(
        customer_id=customer_id, status=status_filter
    )
    return [_booking_resp(b) for b in bookings]


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> BookingResponse:
    """예약 상세 조회."""
    crud = CrmCRUD(session)
    booking = await crud.get_booking(booking_id)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="예약을 찾을 수 없습니다.",
        )
    return _booking_resp(booking)


@router.patch("/bookings/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: str,
    req: BookingUpdate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> BookingResponse:
    """예약 수정 (상태 전환 포함)."""
    crud = CrmCRUD(session)
    booking = await crud.update_booking(booking_id, req)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="예약을 찾을 수 없습니다.",
        )
    return _booking_resp(booking)


# -- Interaction --


@router.post(
    "/interactions", response_model=InteractionResponse, status_code=201
)
async def create_interaction(
    req: InteractionCreate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> InteractionResponse:
    """상호작용 기록."""
    crud = CrmCRUD(session)
    interaction = await crud.create_interaction(req)
    return _interaction_resp(interaction)


@router.get(
    "/customers/{customer_id}/interactions",
    response_model=list[InteractionResponse],
)
async def list_interactions(
    customer_id: str,
    channel: str | None = None,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[InteractionResponse]:
    """고객 상호작용 목록."""
    crud = CrmCRUD(session)
    interactions = await crud.list_interactions(
        customer_id=customer_id, channel=channel
    )
    return [_interaction_resp(i) for i in interactions]
