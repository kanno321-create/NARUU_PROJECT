"""Partner management: CRUD, contract tracking, commission, settlement reports."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.order import Order, PaymentStatus
from app.models.partner import Partner, PartnerType
from app.models.reservation import Reservation
from app.models.review import Review
from app.models.user import User

router = APIRouter(prefix="/partners", tags=["partners"])

MAX_COMMISSION_RATE = 30.0  # 의원급 30% 상한


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PartnerCreate(BaseModel):
    name_ko: str = Field(..., min_length=1, max_length=200)
    name_ja: str | None = None
    type: PartnerType
    address: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    commission_rate: float | None = None
    contract_start: date | None = None
    contract_end: date | None = None
    is_active: bool = True


class PartnerUpdate(BaseModel):
    name_ko: str | None = None
    name_ja: str | None = None
    type: PartnerType | None = None
    address: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    commission_rate: float | None = None
    contract_start: date | None = None
    contract_end: date | None = None
    is_active: bool | None = None


class PartnerOut(BaseModel):
    id: int
    name_ko: str
    name_ja: str | None = None
    type: PartnerType
    address: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    commission_rate: float | None = None
    contract_start: date | None = None
    contract_end: date | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PartnerListResponse(BaseModel):
    items: list[PartnerOut]
    total: int
    page: int
    per_page: int


class SettlementItem(BaseModel):
    order_id: int
    customer_id: int
    total_amount: float
    currency: str
    commission_rate: float
    commission_amount: float
    created_at: str


class SettlementReport(BaseModel):
    partner_id: int
    partner_name: str
    period_start: str
    period_end: str
    total_orders: int
    total_revenue: float
    total_commission: float
    items: list[SettlementItem]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=PartnerListResponse)
async def list_partners(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    type: PartnerType | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = select(Partner)

    if type:
        q = q.where(Partner.type == type)
    if is_active is not None:
        q = q.where(Partner.is_active == is_active)
    if search:
        pattern = f"%{search}%"
        q = q.where(
            (Partner.name_ko.ilike(pattern)) | (Partner.name_ja.ilike(pattern))
        )

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Partner.created_at.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    return PartnerListResponse(
        items=[PartnerOut.model_validate(p) for p in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/stats")
async def partner_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Partner overview statistics."""
    total = (await db.execute(select(func.count(Partner.id)))).scalar() or 0
    active = (
        await db.execute(
            select(func.count(Partner.id)).where(Partner.is_active == True)
        )
    ).scalar() or 0

    # Count by type
    type_q = (
        select(Partner.type, func.count(Partner.id))
        .group_by(Partner.type)
    )
    type_result = await db.execute(type_q)
    by_type = {row[0].value: row[1] for row in type_result.all()}

    # Expiring contracts (within 30 days)
    today = date.today()
    from datetime import timedelta
    expiring_soon = (
        await db.execute(
            select(func.count(Partner.id)).where(
                and_(
                    Partner.contract_end.isnot(None),
                    Partner.contract_end <= today + timedelta(days=30),
                    Partner.contract_end >= today,
                    Partner.is_active == True,
                )
            )
        )
    ).scalar() or 0

    return {
        "total": total,
        "active": active,
        "inactive": total - active,
        "by_type": by_type,
        "expiring_soon": expiring_soon,
    }


@router.get("/{partner_id}", response_model=PartnerOut)
async def get_partner(
    partner_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(404, "Partner not found")
    return PartnerOut.model_validate(partner)


@router.get("/{partner_id}/performance")
async def partner_performance(
    partner_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Get partner's customer/reservation/review performance."""
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(404, "Partner not found")

    # Reservations linked to this partner
    total_reservations = (
        await db.execute(
            select(func.count(Reservation.id)).where(Reservation.partner_id == partner_id)
        )
    ).scalar() or 0

    # Reviews for this partner
    total_reviews = (
        await db.execute(
            select(func.count(Review.id)).where(Review.partner_id == partner_id)
        )
    ).scalar() or 0
    avg_sentiment = (
        await db.execute(
            select(func.avg(Review.sentiment_score)).where(Review.partner_id == partner_id)
        )
    ).scalar()

    # Revenue from orders (where reservation links to this partner)
    revenue_q = (
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .join(Reservation, Order.reservation_id == Reservation.id)
        .where(Reservation.partner_id == partner_id)
    )
    total_revenue = float((await db.execute(revenue_q)).scalar())

    commission_q = (
        select(func.coalesce(func.sum(Order.commission_amount), 0))
        .join(Reservation, Order.reservation_id == Reservation.id)
        .where(Reservation.partner_id == partner_id)
    )
    total_commission = float((await db.execute(commission_q)).scalar())

    return {
        "partner_id": partner_id,
        "total_reservations": total_reservations,
        "total_reviews": total_reviews,
        "avg_sentiment": round(avg_sentiment, 3) if avg_sentiment else None,
        "total_revenue": total_revenue,
        "total_commission": total_commission,
    }


@router.post("", response_model=PartnerOut, status_code=201)
async def create_partner(
    data: PartnerCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if data.commission_rate is not None and data.commission_rate > MAX_COMMISSION_RATE:
        raise HTTPException(
            400,
            f"커미션율은 {MAX_COMMISSION_RATE}%를 초과할 수 없습니다 (의원급 상한).",
        )

    partner = Partner(**data.model_dump())
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return PartnerOut.model_validate(partner)


@router.put("/{partner_id}", response_model=PartnerOut)
async def update_partner(
    partner_id: int,
    data: PartnerUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(404, "Partner not found")

    update_data = data.model_dump(exclude_unset=True)

    if "commission_rate" in update_data and update_data["commission_rate"] is not None:
        if update_data["commission_rate"] > MAX_COMMISSION_RATE:
            raise HTTPException(
                400,
                f"커미션율은 {MAX_COMMISSION_RATE}%를 초과할 수 없습니다 (의원급 상한).",
            )

    for key, value in update_data.items():
        setattr(partner, key, value)

    await db.commit()
    await db.refresh(partner)
    return PartnerOut.model_validate(partner)


@router.delete("/{partner_id}")
async def delete_partner(
    partner_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(404, "Partner not found")

    # Soft delete
    partner.is_active = False
    await db.commit()
    return {"message": "Partner deactivated"}


# ---------------------------------------------------------------------------
# Settlement Report
# ---------------------------------------------------------------------------


@router.get("/{partner_id}/settlement", response_model=SettlementReport)
async def get_settlement(
    partner_id: int,
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Monthly settlement report for a partner."""
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(404, "Partner not found")

    period_start = datetime(year, month, 1)
    if month == 12:
        period_end = datetime(year + 1, 1, 1)
    else:
        period_end = datetime(year, month + 1, 1)

    # Get paid orders linked to reservations at this partner
    orders_q = (
        select(Order)
        .join(Reservation, Order.reservation_id == Reservation.id)
        .where(
            and_(
                Reservation.partner_id == partner_id,
                Order.payment_status == PaymentStatus.PAID,
                Order.created_at >= period_start,
                Order.created_at < period_end,
            )
        )
        .order_by(Order.created_at)
    )
    orders_result = await db.execute(orders_q)
    orders = orders_result.scalars().all()

    items = []
    total_revenue = 0.0
    total_commission = 0.0

    for order in orders:
        rate = float(order.commission_rate or partner.commission_rate or 0)
        commission = float(order.total_amount) * rate / 100
        items.append(
            SettlementItem(
                order_id=order.id,
                customer_id=order.customer_id,
                total_amount=float(order.total_amount),
                currency=order.currency,
                commission_rate=rate,
                commission_amount=round(commission, 2),
                created_at=order.created_at.isoformat(),
            )
        )
        total_revenue += float(order.total_amount)
        total_commission += commission

    return SettlementReport(
        partner_id=partner_id,
        partner_name=partner.name_ko,
        period_start=period_start.strftime("%Y-%m-%d"),
        period_end=period_end.strftime("%Y-%m-%d"),
        total_orders=len(items),
        total_revenue=round(total_revenue, 2),
        total_commission=round(total_commission, 2),
        items=items,
    )
