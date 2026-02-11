"""Partner management routes"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from naruu_api.db import get_db
from naruu_api.routers.auth import get_current_user
from naruu_core.models.partner_models import (
    PartnerCreate, PartnerUpdate, PartnerResponse, PartnerListResponse,
)

router = APIRouter(prefix="/partners", tags=["partners"])


@router.get("", response_model=PartnerListResponse)
async def list_partners(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    conditions = ["is_active = :is_active"]
    params: dict = {"is_active": is_active}

    if search:
        conditions.append("(name_ja ILIKE :search OR name_kr ILIKE :search OR contact_person ILIKE :search)")
        params["search"] = f"%{search}%"
    if category:
        conditions.append("category = :category")
        params["category"] = category

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM naruu.partners WHERE {where}"), params
    )
    total = count_result.scalar()

    result = await db.execute(
        text(f"""
            SELECT * FROM naruu.partners
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
        if isinstance(r.get("services"), str):
            r["services"] = json.loads(r["services"])
        elif r.get("services") is None:
            r["services"] = []
        items.append(PartnerResponse(**r))

    return PartnerListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{partner_id}", response_model=PartnerResponse)
async def get_partner(
    partner_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM naruu.partners WHERE id = :id"), {"id": partner_id}
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Partner not found")
    r = dict(row)
    r["id"] = str(r["id"])
    if isinstance(r.get("services"), str):
        r["services"] = json.loads(r["services"])
    elif r.get("services") is None:
        r["services"] = []
    return PartnerResponse(**r)


@router.post("", response_model=PartnerResponse, status_code=201)
async def create_partner(
    data: PartnerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    count_result = await db.execute(text("SELECT COUNT(*) FROM naruu.partners"))
    count = count_result.scalar() + 1
    code = f"NR-P{count:04d}"

    result = await db.execute(
        text("""
            INSERT INTO naruu.partners (
                code, name_ja, name_kr, name_en, category, sub_category,
                contact_person, phone, email, address_kr, address_ja,
                commission_rate, contract_start, contract_end,
                services, memo
            ) VALUES (
                :code, :name_ja, :name_kr, :name_en, :category, :sub_category,
                :contact_person, :phone, :email, :address_kr, :address_ja,
                :commission_rate, :contract_start, :contract_end,
                :services::jsonb, :memo
            ) RETURNING *
        """),
        {
            "code": code,
            "name_ja": data.name_ja,
            "name_kr": data.name_kr,
            "name_en": data.name_en,
            "category": data.category,
            "sub_category": data.sub_category,
            "contact_person": data.contact_person,
            "phone": data.phone,
            "email": data.email,
            "address_kr": data.address_kr,
            "address_ja": data.address_ja,
            "commission_rate": data.commission_rate,
            "contract_start": data.contract_start,
            "contract_end": data.contract_end,
            "services": json.dumps([s.model_dump() for s in data.services]) if data.services else "[]",
            "memo": data.memo,
        },
    )
    await db.commit()
    row = result.mappings().first()
    r = dict(row)
    r["id"] = str(r["id"])
    if isinstance(r.get("services"), str):
        r["services"] = json.loads(r["services"])
    elif r.get("services") is None:
        r["services"] = []
    return PartnerResponse(**r)


@router.put("/{partner_id}", response_model=PartnerResponse)
async def update_partner(
    partner_id: str,
    data: PartnerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = []
    params = {"id": partner_id}
    for key, value in updates.items():
        if key == "services":
            set_clauses.append(f"{key} = :{key}::jsonb")
            params[key] = json.dumps([s if isinstance(s, dict) else s.model_dump() for s in value]) if value else "[]"
        else:
            set_clauses.append(f"{key} = :{key}")
            params[key] = value

    set_clauses.append("updated_at = NOW()")
    set_sql = ", ".join(set_clauses)

    result = await db.execute(
        text(f"UPDATE naruu.partners SET {set_sql} WHERE id = :id RETURNING *"), params
    )
    await db.commit()
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Partner not found")
    r = dict(row)
    r["id"] = str(r["id"])
    if isinstance(r.get("services"), str):
        r["services"] = json.loads(r["services"])
    elif r.get("services") is None:
        r["services"] = []
    return PartnerResponse(**r)


@router.delete("/{partner_id}", status_code=204)
async def delete_partner(
    partner_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("owner", "manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await db.execute(
        text("UPDATE naruu.partners SET is_active = FALSE, updated_at = NOW() WHERE id = :id"),
        {"id": partner_id},
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Partner not found")
