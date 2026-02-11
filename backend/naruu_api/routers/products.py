"""Tour product management routes"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from naruu_api.db import get_db
from naruu_api.routers.auth import get_current_user
from naruu_core.models.product_models import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    product_type: Optional[str] = None,
    category: Optional[str] = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    conditions = ["is_active = :is_active"]
    params: dict = {"is_active": is_active}

    if search:
        conditions.append("(name_ja ILIKE :search OR name_kr ILIKE :search OR description_ja ILIKE :search)")
        params["search"] = f"%{search}%"
    if product_type:
        conditions.append("product_type = :product_type")
        params["product_type"] = product_type
    if category:
        conditions.append("category = :category")
        params["category"] = category

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM naruu.tour_products WHERE {where}"), params
    )
    total = count_result.scalar()

    result = await db.execute(
        text(f"""
            SELECT * FROM naruu.tour_products
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": page_size, "offset": offset},
    )
    rows = result.mappings().all()

    items = []
    for row in rows:
        r = dict(row)
        r["id"] = str(r["id"])
        for field in ["itinerary", "included_services", "excluded_services", "partner_ids"]:
            if isinstance(r.get(field), str):
                r[field] = json.loads(r[field])
            elif r.get(field) is None:
                r[field] = []
        items.append(ProductResponse(**r))

    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM naruu.tour_products WHERE id = :id"), {"id": product_id}
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    r = dict(row)
    r["id"] = str(r["id"])
    for field in ["itinerary", "included_services", "excluded_services", "partner_ids"]:
        if isinstance(r.get(field), str):
            r[field] = json.loads(r[field])
        elif r.get(field) is None:
            r[field] = []
    return ProductResponse(**r)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    count_result = await db.execute(text("SELECT COUNT(*) FROM naruu.tour_products"))
    count = count_result.scalar() + 1
    code = f"NR-T{count:04d}"

    result = await db.execute(
        text("""
            INSERT INTO naruu.tour_products (
                code, name_ja, name_kr, name_en, product_type, category,
                description_ja, description_kr, duration_days, duration_nights,
                min_participants, max_participants,
                base_price_jpy, base_price_krw,
                itinerary, included_services, excluded_services, partner_ids,
                meeting_point, meeting_time, memo
            ) VALUES (
                :code, :name_ja, :name_kr, :name_en, :product_type, :category,
                :description_ja, :description_kr, :duration_days, :duration_nights,
                :min_participants, :max_participants,
                :base_price_jpy, :base_price_krw,
                :itinerary::jsonb, :included_services::jsonb, :excluded_services::jsonb, :partner_ids::jsonb,
                :meeting_point, :meeting_time, :memo
            ) RETURNING *
        """),
        {
            "code": code,
            "name_ja": data.name_ja,
            "name_kr": data.name_kr,
            "name_en": data.name_en,
            "product_type": data.product_type,
            "category": data.category,
            "description_ja": data.description_ja,
            "description_kr": data.description_kr,
            "duration_days": data.duration_days,
            "duration_nights": data.duration_nights,
            "min_participants": data.min_participants,
            "max_participants": data.max_participants,
            "base_price_jpy": data.base_price_jpy,
            "base_price_krw": data.base_price_krw,
            "itinerary": json.dumps([i.model_dump() for i in data.itinerary]) if data.itinerary else "[]",
            "included_services": json.dumps(data.included_services),
            "excluded_services": json.dumps(data.excluded_services),
            "partner_ids": json.dumps(data.partner_ids),
            "meeting_point": data.meeting_point,
            "meeting_time": data.meeting_time,
            "memo": data.memo,
        },
    )
    await db.commit()
    row = result.mappings().first()
    r = dict(row)
    r["id"] = str(r["id"])
    for field in ["itinerary", "included_services", "excluded_services", "partner_ids"]:
        if isinstance(r.get(field), str):
            r[field] = json.loads(r[field])
        elif r.get(field) is None:
            r[field] = []
    return ProductResponse(**r)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = []
    params = {"id": product_id}
    json_fields = ["itinerary", "included_services", "excluded_services", "partner_ids"]

    for key, value in updates.items():
        if key in json_fields:
            set_clauses.append(f"{key} = :{key}::jsonb")
            if key == "itinerary" and value:
                params[key] = json.dumps([i if isinstance(i, dict) else i.model_dump() for i in value])
            else:
                params[key] = json.dumps(value) if value is not None else "[]"
        else:
            set_clauses.append(f"{key} = :{key}")
            params[key] = value

    set_clauses.append("updated_at = NOW()")
    set_sql = ", ".join(set_clauses)

    result = await db.execute(
        text(f"UPDATE naruu.tour_products SET {set_sql} WHERE id = :id RETURNING *"), params
    )
    await db.commit()
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    r = dict(row)
    r["id"] = str(r["id"])
    for field in json_fields:
        if isinstance(r.get(field), str):
            r[field] = json.loads(r[field])
        elif r.get(field) is None:
            r[field] = []
    return ProductResponse(**r)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("owner", "manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await db.execute(
        text("UPDATE naruu.tour_products SET is_active = FALSE, updated_at = NOW() WHERE id = :id"),
        {"id": product_id},
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not found")
