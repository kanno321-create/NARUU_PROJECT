"""Order/sales management: CRUD, payment status tracking."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.order import Order, PaymentStatus
from app.models.user import User

router = APIRouter(prefix="/orders", tags=["orders"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class OrderCreate(BaseModel):
    customer_id: int
    package_id: int | None = None
    reservation_id: int | None = None
    total_amount: float = Field(..., gt=0)
    currency: str = "JPY"
    payment_method: str | None = None
    commission_rate: float | None = None
    notes: str | None = None


class OrderUpdate(BaseModel):
    payment_status: PaymentStatus | None = None
    payment_method: str | None = None
    commission_rate: float | None = None
    notes: str | None = None


class OrderOut(BaseModel):
    id: int
    customer_id: int
    package_id: int | None = None
    reservation_id: int | None = None
    total_amount: float
    currency: str
    payment_status: PaymentStatus
    payment_method: str | None = None
    commission_rate: float | None = None
    commission_amount: float | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    items: list[OrderOut]
    total: int
    page: int
    per_page: int


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    payment_status: PaymentStatus | None = None,
    currency: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = select(Order)

    if payment_status:
        q = q.where(Order.payment_status == payment_status)
    if currency:
        q = q.where(Order.currency == currency)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Order.created_at.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    return OrderListResponse(
        items=[OrderOut.model_validate(o) for o in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/summary")
async def order_summary(
    year: int = Query(None),
    month: int = Query(None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Monthly revenue summary."""
    now = datetime.now(timezone.utc)
    y = year or now.year
    m = month or now.month

    period_start = datetime(y, m, 1)
    if m == 12:
        period_end = datetime(y + 1, 1, 1)
    else:
        period_end = datetime(y, m + 1, 1)

    base = and_(Order.created_at >= period_start, Order.created_at < period_end)

    total_revenue = float(
        (await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(base)
        )).scalar()
    )
    paid_revenue = float(
        (await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                base, Order.payment_status == PaymentStatus.PAID
            )
        )).scalar()
    )
    total_orders = (await db.execute(select(func.count(Order.id)).where(base))).scalar() or 0
    paid_orders = (
        await db.execute(
            select(func.count(Order.id)).where(base, Order.payment_status == PaymentStatus.PAID)
        )
    ).scalar() or 0
    pending_orders = (
        await db.execute(
            select(func.count(Order.id)).where(base, Order.payment_status == PaymentStatus.PENDING)
        )
    ).scalar() or 0
    total_commission = float(
        (await db.execute(
            select(func.coalesce(func.sum(Order.commission_amount), 0)).where(base)
        )).scalar()
    )

    return {
        "year": y,
        "month": m,
        "total_revenue": total_revenue,
        "paid_revenue": paid_revenue,
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "pending_orders": pending_orders,
        "total_commission": total_commission,
        "net_revenue": paid_revenue - total_commission,
    }


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")
    return OrderOut.model_validate(order)


@router.post("", response_model=OrderOut, status_code=201)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    order_data = data.model_dump()
    if data.commission_rate:
        order_data["commission_amount"] = round(data.total_amount * data.commission_rate / 100, 2)

    order = Order(**order_data)
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return OrderOut.model_validate(order)


@router.put("/{order_id}", response_model=OrderOut)
async def update_order(
    order_id: int,
    data: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")

    update_data = data.model_dump(exclude_unset=True)
    if "commission_rate" in update_data and update_data["commission_rate"]:
        update_data["commission_amount"] = round(
            float(order.total_amount) * update_data["commission_rate"] / 100, 2
        )

    for key, value in update_data.items():
        setattr(order, key, value)

    await db.flush()
    await db.refresh(order)
    return OrderOut.model_validate(order)
