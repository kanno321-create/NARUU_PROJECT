"""Customer CRM routes"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from naruu_api.db import get_db
from naruu_api.routers.auth import get_current_user
from naruu_core.models.customer_models import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse,
)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    source: Optional[str] = None,
    vip_level: Optional[str] = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    conditions = ["is_active = :is_active"]
    params: dict = {"is_active": is_active}

    if search:
        conditions.append("(name_ja ILIKE :search OR name_kr ILIKE :search OR email ILIKE :search OR phone ILIKE :search)")
        params["search"] = f"%{search}%"
    if source:
        conditions.append("customer_source = :source")
        params["source"] = source
    if vip_level:
        conditions.append("vip_level = :vip_level")
        params["vip_level"] = vip_level

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM naruu.customers WHERE {where}"), params
    )
    total = count_result.scalar()

    result = await db.execute(
        text(f"""
            SELECT * FROM naruu.customers
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
        for field in ["medical_interests", "beauty_interests", "tourism_interests", "dietary_restrictions"]:
            if isinstance(r.get(field), str):
                r[field] = json.loads(r[field])
            elif r.get(field) is None:
                r[field] = []
        items.append(CustomerResponse(**r))

    return CustomerListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM naruu.customers WHERE id = :id"), {"id": customer_id}
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found")
    r = dict(row)
    r["id"] = str(r["id"])
    for field in ["medical_interests", "beauty_interests", "tourism_interests", "dietary_restrictions"]:
        if isinstance(r.get(field), str):
            r[field] = json.loads(r[field])
        elif r.get(field) is None:
            r[field] = []
    return CustomerResponse(**r)


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(
    data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Generate customer code
    count_result = await db.execute(text("SELECT COUNT(*) FROM naruu.customers"))
    count = count_result.scalar() + 1
    code = f"NR-C{count:04d}"

    result = await db.execute(
        text("""
            INSERT INTO naruu.customers (
                code, name_ja, name_kr, name_en, gender, birth_date, nationality,
                email, phone, line_user_id, instagram_handle, language_preference,
                medical_interests, beauty_interests, tourism_interests, dietary_restrictions,
                allergies, customer_source, vip_level, memo
            ) VALUES (
                :code, :name_ja, :name_kr, :name_en, :gender, :birth_date, :nationality,
                :email, :phone, :line_user_id, :instagram_handle, :language_preference,
                :medical_interests::jsonb, :beauty_interests::jsonb, :tourism_interests::jsonb, :dietary_restrictions::jsonb,
                :allergies, :customer_source, :vip_level, :memo
            ) RETURNING *
        """),
        {
            "code": code,
            "name_ja": data.name_ja,
            "name_kr": data.name_kr,
            "name_en": data.name_en,
            "gender": data.gender,
            "birth_date": data.birth_date,
            "nationality": data.nationality,
            "email": data.email,
            "phone": data.phone,
            "line_user_id": data.line_user_id,
            "instagram_handle": data.instagram_handle,
            "language_preference": data.language_preference,
            "medical_interests": json.dumps(data.medical_interests),
            "beauty_interests": json.dumps(data.beauty_interests),
            "tourism_interests": json.dumps(data.tourism_interests),
            "dietary_restrictions": json.dumps(data.dietary_restrictions),
            "allergies": data.allergies,
            "customer_source": data.customer_source,
            "vip_level": data.vip_level,
            "memo": data.memo,
        },
    )
    await db.commit()
    row = result.mappings().first()
    r = dict(row)
    r["id"] = str(r["id"])
    for field in ["medical_interests", "beauty_interests", "tourism_interests", "dietary_restrictions"]:
        if isinstance(r.get(field), str):
            r[field] = json.loads(r[field])
        elif r.get(field) is None:
            r[field] = []
    return CustomerResponse(**r)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = []
    params = {"id": customer_id}
    for key, value in updates.items():
        if key in ["medical_interests", "beauty_interests", "tourism_interests", "dietary_restrictions"]:
            set_clauses.append(f"{key} = :{key}::jsonb")
            params[key] = json.dumps(value) if value is not None else "[]"
        else:
            set_clauses.append(f"{key} = :{key}")
            params[key] = value

    set_clauses.append("updated_at = NOW()")
    set_sql = ", ".join(set_clauses)

    result = await db.execute(
        text(f"UPDATE naruu.customers SET {set_sql} WHERE id = :id RETURNING *"), params
    )
    await db.commit()
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found")
    r = dict(row)
    r["id"] = str(r["id"])
    for field in ["medical_interests", "beauty_interests", "tourism_interests", "dietary_restrictions"]:
        if isinstance(r.get(field), str):
            r[field] = json.loads(r[field])
        elif r.get(field) is None:
            r[field] = []
    return CustomerResponse(**r)


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("owner", "manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await db.execute(
        text("UPDATE naruu.customers SET is_active = FALSE, updated_at = NOW() WHERE id = :id"),
        {"id": customer_id},
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
