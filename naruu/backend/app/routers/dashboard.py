"""Dashboard: KPI aggregation, chart data, AI business insights."""

import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.customer import Customer
from app.models.reservation import Reservation, ReservationStatus
from app.models.order import Order
from app.models.content import Content
from app.models.review import Review
from app.models.line_message import LineMessage
from app.models.package import Package
from app.models.tour_route import TourRoute
from app.models.user import User
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class KPIResponse(BaseModel):
    # Revenue
    monthly_revenue: float
    prev_monthly_revenue: float
    revenue_change_pct: float

    # Customers
    new_customers_this_month: int
    prev_new_customers: int
    customer_change: int

    # Reservations
    reservations_this_month: int
    prev_reservations: int
    reservation_change: int

    # Content
    content_published_this_month: int
    prev_content_published: int
    content_change: int

    # Extra KPIs
    total_customers: int
    active_packages: int
    active_routes: int
    pending_reservations: int
    unread_messages: int
    avg_review_score: float | None


class RevenueChartItem(BaseModel):
    month: str
    revenue: float


class ReservationChartItem(BaseModel):
    type: str
    count: int


class CustomerSourceItem(BaseModel):
    source: str
    count: int


class ChartDataResponse(BaseModel):
    revenue_trend: list[RevenueChartItem]
    reservation_by_type: list[ReservationChartItem]
    customer_sources: list[CustomerSourceItem]
    recent_reservations: list[dict]
    recent_reviews: list[dict]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _month_range(offset: int = 0):
    """Return (start, end) of a month. offset=0 → current, -1 → last month."""
    now = datetime.now(timezone.utc)
    year = now.year
    month = now.month + offset
    while month <= 0:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


# ---------------------------------------------------------------------------
# KPI Endpoint
# ---------------------------------------------------------------------------


@router.get("/kpi", response_model=KPIResponse)
async def get_kpi(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    this_start, this_end = _month_range(0)
    prev_start, prev_end = _month_range(-1)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    # Helper coroutines for gather
    async def _sum_revenue(start, end):
        q = select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            and_(Order.created_at >= start, Order.created_at < end)
        )
        return float((await db.execute(q)).scalar())

    async def _count(model_col, *filters):
        q = select(func.count(model_col)).where(*filters) if filters else select(func.count(model_col))
        return (await db.execute(q)).scalar() or 0

    # Run ALL independent queries in parallel
    (
        monthly_revenue,
        prev_monthly_revenue,
        new_customers,
        prev_customers,
        reservations,
        prev_reservations,
        content_pub,
        prev_content,
        total_customers,
        active_packages,
        active_routes,
        pending_reservations,
        unread_messages,
        avg_review,
    ) = await asyncio.gather(
        _sum_revenue(this_start, this_end),
        _sum_revenue(prev_start, prev_end),
        _count(Customer.id, and_(Customer.created_at >= this_start, Customer.created_at < this_end)),
        _count(Customer.id, and_(Customer.created_at >= prev_start, Customer.created_at < prev_end)),
        _count(Reservation.id, and_(Reservation.created_at >= this_start, Reservation.created_at < this_end)),
        _count(Reservation.id, and_(Reservation.created_at >= prev_start, Reservation.created_at < prev_end)),
        _count(Content.id, and_(Content.created_at >= this_start, Content.created_at < this_end, Content.status == "published")),
        _count(Content.id, and_(Content.created_at >= prev_start, Content.created_at < prev_end, Content.status == "published")),
        _count(Customer.id),
        _count(Package.id, Package.is_active == True),
        _count(TourRoute.id, TourRoute.status != "archived"),
        _count(Reservation.id, Reservation.status == ReservationStatus.PENDING),
        _count(LineMessage.id, and_(LineMessage.direction == "in", LineMessage.created_at >= yesterday)),
        db.execute(select(func.avg(Review.sentiment_score))),
    )

    # avg_review is a Result object from gather; extract scalar
    avg_review_val = avg_review.scalar() if hasattr(avg_review, 'scalar') else avg_review

    revenue_change_pct = (
        round((monthly_revenue - prev_monthly_revenue) / prev_monthly_revenue * 100, 1)
        if prev_monthly_revenue > 0
        else 0
    )

    return KPIResponse(
        monthly_revenue=monthly_revenue,
        prev_monthly_revenue=prev_monthly_revenue,
        revenue_change_pct=revenue_change_pct,
        new_customers_this_month=new_customers,
        prev_new_customers=prev_customers,
        customer_change=new_customers - prev_customers,
        reservations_this_month=reservations,
        prev_reservations=prev_reservations,
        reservation_change=reservations - prev_reservations,
        content_published_this_month=content_pub,
        prev_content_published=prev_content,
        content_change=content_pub - prev_content,
        total_customers=total_customers,
        active_packages=active_packages,
        active_routes=active_routes,
        pending_reservations=pending_reservations,
        unread_messages=unread_messages,
        avg_review_score=round(avg_review_val, 2) if avg_review_val else None,
    )


# ---------------------------------------------------------------------------
# Chart Data Endpoint
# ---------------------------------------------------------------------------


@router.get("/charts", response_model=ChartDataResponse)
async def get_chart_data(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    # Revenue trend (last 6 months) — single GROUP BY query
    six_months_ago_start, _ = _month_range(-5)
    _, current_month_end = _month_range(0)

    revenue_q = (
        select(
            extract("year", Order.created_at).label("yr"),
            extract("month", Order.created_at).label("mo"),
            func.coalesce(func.sum(Order.total_amount), 0),
        )
        .where(and_(Order.created_at >= six_months_ago_start, Order.created_at < current_month_end))
        .group_by("yr", "mo")
        .order_by("yr", "mo")
    )
    revenue_rows = (await db.execute(revenue_q)).all()
    revenue_map = {(int(r[0]), int(r[1])): float(r[2]) for r in revenue_rows}

    revenue_trend = []
    for offset in range(-5, 1):
        start, _ = _month_range(offset)
        key = (start.year, start.month)
        revenue_trend.append(
            RevenueChartItem(
                month=start.strftime("%Y-%m"),
                revenue=revenue_map.get(key, 0.0),
            )
        )

    # Reservation by type
    type_q = (
        select(Reservation.type, func.count(Reservation.id))
        .group_by(Reservation.type)
    )
    type_result = await db.execute(type_q)
    reservation_by_type = [
        ReservationChartItem(type=row[0].value if hasattr(row[0], 'value') else str(row[0]), count=row[1])
        for row in type_result.all()
    ]

    # Customer source (nationality distribution)
    source_q = (
        select(Customer.nationality, func.count(Customer.id))
        .group_by(Customer.nationality)
        .order_by(func.count(Customer.id).desc())
        .limit(5)
    )
    source_result = await db.execute(source_q)
    customer_sources = [
        CustomerSourceItem(source=row[0] or "unknown", count=row[1])
        for row in source_result.all()
    ]

    # Recent reservations (last 5)
    recent_res_q = (
        select(Reservation)
        .order_by(Reservation.created_at.desc())
        .limit(5)
    )
    recent_res = (await db.execute(recent_res_q)).scalars().all()
    recent_reservations = [
        {
            "id": r.id,
            "customer_id": r.customer_id,
            "type": r.type.value,
            "status": r.status.value,
            "date": r.reservation_date.isoformat(),
        }
        for r in recent_res
    ]

    # Recent reviews (last 5)
    recent_rev_q = (
        select(Review)
        .order_by(Review.created_at.desc())
        .limit(5)
    )
    recent_rev = (await db.execute(recent_rev_q)).scalars().all()
    recent_reviews = [
        {
            "id": r.id,
            "platform": r.platform.value if hasattr(r.platform, 'value') else str(r.platform),
            "sentiment_score": r.sentiment_score,
            "created_at": r.created_at.isoformat(),
        }
        for r in recent_rev
    ]

    return ChartDataResponse(
        revenue_trend=revenue_trend,
        reservation_by_type=reservation_by_type,
        customer_sources=customer_sources,
        recent_reservations=recent_reservations,
        recent_reviews=recent_reviews,
    )


# ---------------------------------------------------------------------------
# AI Business Insights
# ---------------------------------------------------------------------------


@router.get("/ai-insights")
async def get_ai_insights(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Generate AI-powered business insights based on current data."""
    # Gather summary data
    this_start, this_end = _month_range(0)
    prev_start, prev_end = _month_range(-1)

    # Quick stats
    monthly_rev = float(
        (
            await db.execute(
                select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                    and_(Order.created_at >= this_start, Order.created_at < this_end)
                )
            )
        ).scalar()
    )
    new_custs = (
        await db.execute(
            select(func.count(Customer.id)).where(
                and_(Customer.created_at >= this_start, Customer.created_at < this_end)
            )
        )
    ).scalar() or 0
    total_res = (
        await db.execute(
            select(func.count(Reservation.id)).where(
                and_(Reservation.created_at >= this_start, Reservation.created_at < this_end)
            )
        )
    ).scalar() or 0
    pending_res = (
        await db.execute(
            select(func.count(Reservation.id)).where(
                Reservation.status == ReservationStatus.PENDING
            )
        )
    ).scalar() or 0

    system_prompt = (
        "あなたはNARUU（ナル）のビジネスアナリストAIです。"
        "大邱の美容観光・医療観光ビジネスのデータを分析し、"
        "実用的なビジネスインサイトを日本語で提供してください。"
        "簡潔に3-5つのポイントで回答してください。"
    )

    user_message = (
        f"今月のビジネスデータ:\n"
        f"- 月間売上: ¥{monthly_rev:,.0f}\n"
        f"- 新規顧客: {new_custs}名\n"
        f"- 予約件数: {total_res}件\n"
        f"- 保留中の予約: {pending_res}件\n\n"
        f"このデータに基づいて、ビジネスインサイトと改善提案をお願いします。"
    )

    ai = get_ai_service()
    reply = await ai.chat(user_message, system_prompt=system_prompt, max_tokens=800)

    return {"insights": reply or "AI分析が利用できません。APIキーを確認してください。"}
