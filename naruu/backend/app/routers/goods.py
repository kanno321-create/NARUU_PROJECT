"""Goods shop: CRUD, inventory management, catalog."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.goods import Goods, GoodsCategory
from app.models.user import User

router = APIRouter(prefix="/goods", tags=["goods"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class GoodsCreate(BaseModel):
    name_ja: str = Field(..., min_length=1, max_length=200)
    name_ko: str = Field(..., min_length=1, max_length=200)
    description_ja: str | None = None
    description_ko: str | None = None
    category: GoodsCategory
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(0, ge=0)
    image_urls: list[str] | None = None
    is_active: bool = True


class GoodsUpdate(BaseModel):
    name_ja: str | None = None
    name_ko: str | None = None
    description_ja: str | None = None
    description_ko: str | None = None
    category: GoodsCategory | None = None
    price: float | None = None
    stock_quantity: int | None = None
    image_urls: list[str] | None = None
    is_active: bool | None = None


class GoodsOut(BaseModel):
    id: int
    name_ja: str
    name_ko: str
    description_ja: str | None = None
    description_ko: str | None = None
    category: GoodsCategory
    price: float
    stock_quantity: int
    image_urls: list[str] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GoodsListResponse(BaseModel):
    items: list[GoodsOut]
    total: int
    page: int
    per_page: int


class StockAdjust(BaseModel):
    adjustment: int  # positive = add, negative = subtract
    reason: str | None = None


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=GoodsListResponse)
async def list_goods(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: GoodsCategory | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    low_stock: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = select(Goods)

    if category:
        q = q.where(Goods.category == category)
    if is_active is not None:
        q = q.where(Goods.is_active == is_active)
    if search:
        pattern = f"%{search}%"
        q = q.where(
            (Goods.name_ja.ilike(pattern)) | (Goods.name_ko.ilike(pattern))
        )
    if low_stock:
        q = q.where(Goods.stock_quantity <= 5)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Goods.created_at.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    return GoodsListResponse(
        items=[GoodsOut.model_validate(g) for g in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/stats")
async def goods_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    total = (await db.execute(select(func.count(Goods.id)))).scalar() or 0
    active = (
        await db.execute(
            select(func.count(Goods.id)).where(Goods.is_active == True)
        )
    ).scalar() or 0
    low_stock = (
        await db.execute(
            select(func.count(Goods.id)).where(
                Goods.stock_quantity <= 5, Goods.is_active == True
            )
        )
    ).scalar() or 0
    out_of_stock = (
        await db.execute(
            select(func.count(Goods.id)).where(
                Goods.stock_quantity == 0, Goods.is_active == True
            )
        )
    ).scalar() or 0

    # By category
    cat_q = select(Goods.category, func.count(Goods.id)).group_by(Goods.category)
    cat_result = await db.execute(cat_q)
    by_category = {row[0].value: row[1] for row in cat_result.all()}

    # Total inventory value
    total_value = (
        await db.execute(
            select(func.sum(Goods.price * Goods.stock_quantity)).where(Goods.is_active == True)
        )
    ).scalar() or 0

    return {
        "total": total,
        "active": active,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "by_category": by_category,
        "total_inventory_value": float(total_value),
    }


@router.get("/{goods_id}", response_model=GoodsOut)
async def get_goods(
    goods_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Goods).where(Goods.id == goods_id))
    goods = result.scalar_one_or_none()
    if not goods:
        raise HTTPException(404, "Goods not found")
    return GoodsOut.model_validate(goods)


@router.post("", response_model=GoodsOut, status_code=201)
async def create_goods(
    data: GoodsCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    goods = Goods(**data.model_dump())
    db.add(goods)
    await db.commit()
    await db.refresh(goods)
    return GoodsOut.model_validate(goods)


@router.put("/{goods_id}", response_model=GoodsOut)
async def update_goods(
    goods_id: int,
    data: GoodsUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Goods).where(Goods.id == goods_id))
    goods = result.scalar_one_or_none()
    if not goods:
        raise HTTPException(404, "Goods not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(goods, key, value)

    await db.commit()
    await db.refresh(goods)
    return GoodsOut.model_validate(goods)


@router.post("/{goods_id}/stock", response_model=GoodsOut)
async def adjust_stock(
    goods_id: int,
    data: StockAdjust,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Adjust stock quantity (positive to add, negative to subtract)."""
    result = await db.execute(select(Goods).where(Goods.id == goods_id))
    goods = result.scalar_one_or_none()
    if not goods:
        raise HTTPException(404, "Goods not found")

    new_qty = goods.stock_quantity + data.adjustment
    if new_qty < 0:
        raise HTTPException(400, f"재고 부족: 현재 {goods.stock_quantity}, 조정 {data.adjustment}")

    goods.stock_quantity = new_qty
    await db.commit()
    await db.refresh(goods)
    return GoodsOut.model_validate(goods)


@router.delete("/{goods_id}")
async def delete_goods(
    goods_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Goods).where(Goods.id == goods_id))
    goods = result.scalar_one_or_none()
    if not goods:
        raise HTTPException(404, "Goods not found")

    goods.is_active = False
    await db.commit()
    return {"message": "Goods deactivated"}
