"""Customer CRUD + search + journey timeline routes."""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.customer import Customer
from app.models.line_message import LineMessage
from app.models.order import Order
from app.models.reservation import Reservation
from app.models.review import Review
from app.models.user import User

router = APIRouter(prefix="/customers", tags=["customers"])


# ── Schemas ──────────────────────────────────────


class CustomerCreate(BaseModel):
    name_ja: str
    name_ko: str | None = None
    email: str | None = None
    phone: str | None = None
    line_user_id: str | None = None
    nationality: str = "JP"
    visa_type: str | None = None
    first_visit_date: date | None = None
    preferred_language: str = "ja"
    notes: str | None = None
    tags: list[str] | None = None


class CustomerUpdate(BaseModel):
    name_ja: str | None = None
    name_ko: str | None = None
    email: str | None = None
    phone: str | None = None
    line_user_id: str | None = None
    nationality: str | None = None
    visa_type: str | None = None
    first_visit_date: date | None = None
    preferred_language: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class CustomerResponse(BaseModel):
    id: int
    name_ja: str
    name_ko: str | None
    email: str | None
    phone: str | None
    line_user_id: str | None
    nationality: str
    visa_type: str | None
    first_visit_date: date | None
    preferred_language: str
    notes: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int


class JourneyEvent(BaseModel):
    """Single event in the customer journey timeline."""
    id: int
    event_type: str  # reservation, order, review, line_message
    title: str
    description: str | None
    status: str | None
    date: datetime


class CustomerDetailResponse(CustomerResponse):
    """Customer detail with journey timeline."""
    journey: list[JourneyEvent]
    stats: dict


# ── Endpoints ────────────────────────────────────


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="이름/이메일/LINE ID 검색"),
    tag: str | None = Query(None, description="태그 필터"),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """고객 목록 조회 (검색/태그 필터링 지원)."""
    query = select(Customer)

    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Customer.name_ja.ilike(pattern),
                Customer.name_ko.ilike(pattern),
                Customer.email.ilike(pattern),
                Customer.line_user_id.ilike(pattern),
                Customer.phone.ilike(pattern),
            )
        )

    if tag:
        query = query.where(Customer.tags.any(tag))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Customer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return CustomerListResponse(
        items=[CustomerResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    body: CustomerCreate,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """신규 고객 등록."""
    if body.line_user_id:
        existing = await db.execute(
            select(Customer).where(Customer.line_user_id == body.line_user_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 등록된 LINE 사용자입니다",
            )

    customer = Customer(**body.model_dump())
    db.add(customer)
    await db.flush()
    await db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer(
    customer_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """고객 상세 조회 + 여정 타임라인."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다",
        )

    journey = await _build_journey(db, customer_id)
    stats = await _build_stats(db, customer_id)

    resp = CustomerDetailResponse.model_validate(customer)
    resp.journey = journey
    resp.stats = stats
    return resp


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """고객 정보 수정."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    await db.flush()
    await db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """고객 삭제."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다",
        )

    await db.delete(customer)


# ── Journey Builder ──────────────────────────────


async def _build_journey(db: AsyncSession, customer_id: int) -> list[JourneyEvent]:
    """Build timeline of all customer interactions."""
    events: list[JourneyEvent] = []

    # Reservations
    reservations = await db.execute(
        select(Reservation)
        .where(Reservation.customer_id == customer_id)
        .order_by(Reservation.reservation_date.desc())
    )
    for r in reservations.scalars():
        events.append(JourneyEvent(
            id=r.id,
            event_type="reservation",
            title=f"예약 ({r.type.value})",
            description=r.notes_ko or r.notes_ja,
            status=r.status.value,
            date=r.reservation_date,
        ))

    # Orders
    orders = await db.execute(
        select(Order)
        .where(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc())
    )
    for o in orders.scalars():
        events.append(JourneyEvent(
            id=o.id,
            event_type="order",
            title=f"주문 (¥{o.total_amount:,.0f})",
            description=o.notes,
            status=o.payment_status.value,
            date=o.created_at,
        ))

    # Reviews
    reviews = await db.execute(
        select(Review)
        .where(Review.customer_id == customer_id)
        .order_by(Review.created_at.desc())
    )
    for rv in reviews.scalars():
        events.append(JourneyEvent(
            id=rv.id,
            event_type="review",
            title=f"리뷰 ({rv.platform.value}) {'⭐' * int(rv.rating or 0)}",
            description=rv.content_ko or rv.content_ja,
            status="published" if rv.is_published else "draft",
            date=rv.created_at,
        ))

    # LINE messages (last 20)
    messages = await db.execute(
        select(LineMessage)
        .where(LineMessage.customer_id == customer_id)
        .order_by(LineMessage.created_at.desc())
        .limit(20)
    )
    for m in messages.scalars():
        direction = "수신" if m.direction.value == "in" else "발신"
        ai_tag = " [AI]" if m.ai_generated else ""
        events.append(JourneyEvent(
            id=m.id,
            event_type="line_message",
            title=f"LINE {direction}{ai_tag}",
            description=m.content[:100] if m.content else None,
            status=None,
            date=m.created_at,
        ))

    # Sort by date descending
    events.sort(key=lambda e: e.date, reverse=True)
    return events


async def _build_stats(db: AsyncSession, customer_id: int) -> dict:
    """Build customer stats summary."""
    # Total orders + revenue
    order_result = await db.execute(
        select(func.count(), func.coalesce(func.sum(Order.total_amount), 0))
        .where(Order.customer_id == customer_id)
    )
    order_count, total_revenue = order_result.one()

    # Reservation count
    res_result = await db.execute(
        select(func.count())
        .where(Reservation.customer_id == customer_id)
    )
    reservation_count = res_result.scalar() or 0

    # Review count
    rev_result = await db.execute(
        select(func.count())
        .where(Review.customer_id == customer_id)
    )
    review_count = rev_result.scalar() or 0

    # LINE message count
    msg_result = await db.execute(
        select(func.count())
        .where(LineMessage.customer_id == customer_id)
    )
    message_count = msg_result.scalar() or 0

    return {
        "total_orders": order_count,
        "total_revenue": float(total_revenue),
        "total_reservations": reservation_count,
        "total_reviews": review_count,
        "total_messages": message_count,
    }
