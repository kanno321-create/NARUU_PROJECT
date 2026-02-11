"""Booking management routes"""

import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from naruu_api.db import get_db
from naruu_api.routers.auth import get_current_user
from naruu_core.models.booking_models import (
    BookingCreate, BookingUpdate, BookingResponse, BookingListResponse,
    BookingItemCreate, BookingItemResponse,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _parse_booking_row(row) -> dict:
    r = dict(row)
    r["id"] = str(r["id"])
    if r.get("customer_id"):
        r["customer_id"] = str(r["customer_id"])
    if r.get("product_id"):
        r["product_id"] = str(r["product_id"])
    if r.get("assigned_guide_id"):
        r["assigned_guide_id"] = str(r["assigned_guide_id"])
    return r


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    conditions = ["1=1"]
    params: dict = {}

    if status:
        conditions.append("status = :status")
        params["status"] = status
    if customer_id:
        conditions.append("customer_id = :customer_id")
        params["customer_id"] = customer_id
    if date_from:
        conditions.append("tour_date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        conditions.append("tour_date <= :date_to")
        params["date_to"] = date_to

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM naruu.bookings WHERE {where}"), params
    )
    total = count_result.scalar()

    result = await db.execute(
        text(f"""
            SELECT * FROM naruu.bookings
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": page_size, "offset": offset},
    )
    rows = result.mappings().all()
    items = [BookingResponse(**_parse_booking_row(row)) for row in rows]

    return BookingListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM naruu.bookings WHERE id = :id"), {"id": booking_id}
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")
    return BookingResponse(**_parse_booking_row(row))


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    year = datetime.now().year
    count_result = await db.execute(
        text("SELECT COUNT(*) FROM naruu.bookings WHERE EXTRACT(YEAR FROM created_at) = :year"),
        {"year": year},
    )
    count = count_result.scalar() + 1
    booking_no = f"NR-B{year}-{count:04d}"

    result = await db.execute(
        text("""
            INSERT INTO naruu.bookings (
                booking_no, customer_id, product_id, status,
                tour_date, tour_end_date, num_adults, num_children,
                total_price_jpy, total_price_krw, exchange_rate,
                payment_method, payment_status,
                assigned_guide_id, special_requests, internal_memo
            ) VALUES (
                :booking_no, :customer_id, :product_id, :status,
                :tour_date, :tour_end_date, :num_adults, :num_children,
                :total_price_jpy, :total_price_krw, :exchange_rate,
                :payment_method, :payment_status,
                :assigned_guide_id, :special_requests, :internal_memo
            ) RETURNING *
        """),
        {
            "booking_no": booking_no,
            "customer_id": data.customer_id,
            "product_id": data.product_id,
            "status": data.status or "inquiry",
            "tour_date": data.tour_date,
            "tour_end_date": data.tour_end_date,
            "num_adults": data.num_adults,
            "num_children": data.num_children,
            "total_price_jpy": data.total_price_jpy,
            "total_price_krw": data.total_price_krw,
            "exchange_rate": data.exchange_rate,
            "payment_method": data.payment_method,
            "payment_status": data.payment_status or "pending",
            "assigned_guide_id": data.assigned_guide_id,
            "special_requests": data.special_requests,
            "internal_memo": data.internal_memo,
        },
    )
    await db.commit()
    row = result.mappings().first()
    return BookingResponse(**_parse_booking_row(row))


@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: str,
    data: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = []
    params = {"id": booking_id}
    for key, value in updates.items():
        set_clauses.append(f"{key} = :{key}")
        params[key] = value

    set_clauses.append("updated_at = NOW()")
    set_sql = ", ".join(set_clauses)

    result = await db.execute(
        text(f"UPDATE naruu.bookings SET {set_sql} WHERE id = :id RETURNING *"), params
    )
    await db.commit()
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")
    return BookingResponse(**_parse_booking_row(row))


@router.delete("/{booking_id}", status_code=204)
async def cancel_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("owner", "manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await db.execute(
        text("UPDATE naruu.bookings SET status = 'cancelled', updated_at = NOW() WHERE id = :id"),
        {"id": booking_id},
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Booking not found")


# --- Booking Items ---


@router.get("/{booking_id}/items", response_model=list[BookingItemResponse])
async def list_booking_items(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM naruu.booking_items WHERE booking_id = :booking_id ORDER BY created_at"),
        {"booking_id": booking_id},
    )
    rows = result.mappings().all()
    items = []
    for row in rows:
        r = dict(row)
        r["id"] = str(r["id"])
        r["booking_id"] = str(r["booking_id"])
        if r.get("partner_id"):
            r["partner_id"] = str(r["partner_id"])
        items.append(BookingItemResponse(**r))
    return items


@router.post("/{booking_id}/items", response_model=BookingItemResponse, status_code=201)
async def add_booking_item(
    booking_id: str,
    data: BookingItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        text("""
            INSERT INTO naruu.booking_items (
                booking_id, partner_id, service_name, service_type,
                unit_price_jpy, unit_price_krw, quantity,
                commission_rate, commission_amount_krw, memo
            ) VALUES (
                :booking_id, :partner_id, :service_name, :service_type,
                :unit_price_jpy, :unit_price_krw, :quantity,
                :commission_rate, :commission_amount_krw, :memo
            ) RETURNING *
        """),
        {
            "booking_id": booking_id,
            "partner_id": data.partner_id,
            "service_name": data.service_name,
            "service_type": data.service_type,
            "unit_price_jpy": data.unit_price_jpy,
            "unit_price_krw": data.unit_price_krw,
            "quantity": data.quantity,
            "commission_rate": data.commission_rate,
            "commission_amount_krw": data.commission_amount_krw,
            "memo": data.memo,
        },
    )
    await db.commit()
    row = result.mappings().first()
    r = dict(row)
    r["id"] = str(r["id"])
    r["booking_id"] = str(r["booking_id"])
    if r.get("partner_id"):
        r["partner_id"] = str(r["partner_id"])
    return BookingItemResponse(**r)
