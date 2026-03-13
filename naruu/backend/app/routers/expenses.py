"""Expense management: CRUD, monthly summaries, P&L data."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.expense import Expense
from app.models.order import Order
from app.models.user import User

router = APIRouter(prefix="/expenses", tags=["expenses"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ExpenseCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    vendor_name: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    currency: str = "KRW"
    description: str | None = None
    receipt_url: str | None = None


class ExpenseUpdate(BaseModel):
    category: str | None = None
    vendor_name: str | None = None
    amount: float | None = None
    currency: str | None = None
    description: str | None = None
    receipt_url: str | None = None


class ExpenseOut(BaseModel):
    id: int
    category: str
    vendor_name: str
    amount: float
    currency: str
    description: str | None = None
    receipt_url: str | None = None
    approved_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpenseListResponse(BaseModel):
    items: list[ExpenseOut]
    total: int
    page: int
    per_page: int


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=ExpenseListResponse)
async def list_expenses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = select(Expense)

    if category:
        q = q.where(Expense.category == category)
    if search:
        pattern = f"%{search}%"
        q = q.where(
            (Expense.vendor_name.ilike(pattern)) | (Expense.description.ilike(pattern))
        )

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Expense.created_at.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    return ExpenseListResponse(
        items=[ExpenseOut.model_validate(e) for e in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/summary")
async def expense_summary(
    year: int = Query(None),
    month: int = Query(None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Monthly expense summary."""
    now = datetime.now(timezone.utc)
    y = year or now.year
    m = month or now.month

    period_start = datetime(y, m, 1)
    if m == 12:
        period_end = datetime(y + 1, 1, 1)
    else:
        period_end = datetime(y, m + 1, 1)

    base = and_(Expense.created_at >= period_start, Expense.created_at < period_end)

    total_expenses = float(
        (await db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(base)
        )).scalar()
    )
    expense_count = (await db.execute(select(func.count(Expense.id)).where(base))).scalar() or 0

    # By category
    cat_q = (
        select(Expense.category, func.sum(Expense.amount), func.count(Expense.id))
        .where(base)
        .group_by(Expense.category)
    )
    cat_result = await db.execute(cat_q)
    by_category = [
        {"category": row[0], "total": float(row[1]), "count": row[2]}
        for row in cat_result.all()
    ]

    return {
        "year": y,
        "month": m,
        "total_expenses": total_expenses,
        "expense_count": expense_count,
        "by_category": by_category,
    }


@router.get("/pnl")
async def profit_and_loss(
    year: int = Query(None),
    month: int = Query(None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Monthly Profit & Loss statement."""
    now = datetime.now(timezone.utc)
    y = year or now.year
    m = month or now.month

    period_start = datetime(y, m, 1)
    if m == 12:
        period_end = datetime(y + 1, 1, 1)
    else:
        period_end = datetime(y, m + 1, 1)

    order_base = and_(Order.created_at >= period_start, Order.created_at < period_end)
    expense_base = and_(Expense.created_at >= period_start, Expense.created_at < period_end)

    # Revenue
    total_revenue = float(
        (await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(order_base)
        )).scalar()
    )
    total_commission = float(
        (await db.execute(
            select(func.coalesce(func.sum(Order.commission_amount), 0)).where(order_base)
        )).scalar()
    )

    # Expenses
    total_expenses = float(
        (await db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(expense_base)
        )).scalar()
    )

    net_revenue = total_revenue - total_commission
    profit = net_revenue - total_expenses

    return {
        "year": y,
        "month": m,
        "revenue": {
            "gross": total_revenue,
            "commission": total_commission,
            "net": net_revenue,
        },
        "expenses": total_expenses,
        "profit": profit,
        "profit_margin": round(profit / total_revenue * 100, 1) if total_revenue > 0 else 0,
    }


@router.get("/{expense_id}", response_model=ExpenseOut)
async def get_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(404, "Expense not found")
    return ExpenseOut.model_validate(expense)


@router.post("", response_model=ExpenseOut, status_code=201)
async def create_expense(
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    expense = Expense(**data.model_dump())
    db.add(expense)
    await db.flush()
    await db.refresh(expense)
    return ExpenseOut.model_validate(expense)


@router.put("/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(404, "Expense not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(expense, key, value)

    await db.flush()
    await db.refresh(expense)
    return ExpenseOut.model_validate(expense)


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(404, "Expense not found")

    await db.delete(expense)
    await db.flush()
    return {"message": "Expense deleted"}
