"""Package management: CRUD, quote builder, AI recommendation, exchange rate."""

import enum
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.package import Currency, Package, PackageCategory
from app.models.user import User
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/packages", tags=["packages"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PackageCreate(BaseModel):
    name_ja: str = Field(..., min_length=1, max_length=200)
    name_ko: str = Field(..., min_length=1, max_length=200)
    description_ja: str | None = None
    description_ko: str | None = None
    category: PackageCategory
    base_price: float | None = None
    currency: Currency = Currency.JPY
    duration_days: int | None = None
    includes: list[str] | None = None
    is_active: bool = True


class PackageUpdate(BaseModel):
    name_ja: str | None = None
    name_ko: str | None = None
    description_ja: str | None = None
    description_ko: str | None = None
    category: PackageCategory | None = None
    base_price: float | None = None
    currency: Currency | None = None
    duration_days: int | None = None
    includes: list[str] | None = None
    is_active: bool | None = None


class PackageOut(BaseModel):
    id: int
    name_ja: str
    name_ko: str
    description_ja: str | None = None
    description_ko: str | None = None
    category: PackageCategory
    base_price: float | None = None
    currency: Currency
    duration_days: int | None = None
    includes: list[str] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PackageListResponse(BaseModel):
    items: list[PackageOut]
    total: int
    page: int
    per_page: int


# --- Quote Builder Schemas ---


class QuoteItem(BaseModel):
    package_id: int
    quantity: int = 1
    custom_price: float | None = None  # override per-item price


class QuoteRequest(BaseModel):
    items: list[QuoteItem] = Field(..., min_length=1)
    target_currency: Currency = Currency.JPY
    customer_name: str | None = None
    notes: str | None = None
    discount_percent: float = 0


class QuoteLineItem(BaseModel):
    package_name_ja: str
    package_name_ko: str
    category: PackageCategory
    quantity: int
    unit_price: float
    subtotal: float
    currency: Currency


class QuoteResponse(BaseModel):
    line_items: list[QuoteLineItem]
    subtotal: float
    discount_percent: float
    discount_amount: float
    total: float
    target_currency: Currency
    exchange_rate: float | None = None
    total_converted: float | None = None
    converted_currency: Currency | None = None
    customer_name: str | None = None
    notes: str | None = None
    generated_at: datetime


# --- AI Recommendation ---


class RecommendRequest(BaseModel):
    customer_tags: list[str] | None = None
    budget_jpy: float | None = None
    duration_days: int | None = None
    interests: str | None = None


class RecommendResponse(BaseModel):
    recommendation: str
    suggested_package_ids: list[int]


# --- Exchange Rate ---

# Fallback rate — updated daily in production via external API
DEFAULT_KRW_PER_JPY = 9.5  # 1 JPY ≈ 9.5 KRW (approximate)

# In-memory cache with 1-hour TTL
_exchange_cache: dict = {"rate": None, "fetched_at": None}


async def get_exchange_rate() -> float:
    """Get JPY->KRW exchange rate. Uses external API with 1-hour cache and fallback."""
    import httpx

    now = datetime.now(timezone.utc)
    cached_rate = _exchange_cache["rate"]
    cached_at = _exchange_cache["fetched_at"]

    if cached_rate is not None and cached_at is not None:
        elapsed = (now - cached_at).total_seconds()
        if elapsed < 3600:
            return cached_rate

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://api.exchangerate-api.com/v4/latest/JPY"
            )
            if resp.status_code == 200:
                data = resp.json()
                rate = data["rates"].get("KRW", DEFAULT_KRW_PER_JPY)
                _exchange_cache["rate"] = rate
                _exchange_cache["fetched_at"] = now
                return rate
    except Exception:
        pass

    # If cache has a stale value, return it rather than default
    if cached_rate is not None:
        return cached_rate
    return DEFAULT_KRW_PER_JPY


# ---------------------------------------------------------------------------
# CRUD Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=PackageListResponse)
async def list_packages(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: PackageCategory | None = None,
    search: str | None = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """List packages with filtering and pagination."""
    q = select(Package)

    if active_only:
        q = q.where(Package.is_active == True)
    if category:
        q = q.where(Package.category == category)
    if search:
        pattern = f"%{search}%"
        q = q.where(
            (Package.name_ja.ilike(pattern))
            | (Package.name_ko.ilike(pattern))
            | (Package.description_ja.ilike(pattern))
        )

    # Count
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    q = q.order_by(Package.created_at.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    return PackageListResponse(
        items=[PackageOut.model_validate(p) for p in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/exchange-rate")
async def exchange_rate():
    """Get current JPY→KRW exchange rate."""
    rate = await get_exchange_rate()
    return {"jpy_to_krw": rate, "krw_to_jpy": round(1 / rate, 6)}


@router.get("/{package_id}", response_model=PackageOut)
async def get_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Get single package by ID."""
    result = await db.execute(select(Package).where(Package.id == package_id))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(404, "Package not found")
    return PackageOut.model_validate(pkg)


@router.post("", response_model=PackageOut, status_code=201)
async def create_package(
    data: PackageCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Create a new package."""
    pkg = Package(**data.model_dump())
    db.add(pkg)
    await db.flush()
    await db.refresh(pkg)
    return PackageOut.model_validate(pkg)


@router.put("/{package_id}", response_model=PackageOut)
async def update_package(
    package_id: int,
    data: PackageUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Update an existing package."""
    result = await db.execute(select(Package).where(Package.id == package_id))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(404, "Package not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pkg, key, value)

    await db.flush()
    await db.refresh(pkg)
    return PackageOut.model_validate(pkg)


@router.delete("/{package_id}")
async def delete_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Soft-delete: deactivate a package."""
    result = await db.execute(select(Package).where(Package.id == package_id))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(404, "Package not found")

    pkg.is_active = False
    await db.flush()
    return {"message": "Package deactivated"}


# ---------------------------------------------------------------------------
# Quote Builder
# ---------------------------------------------------------------------------


@router.post("/quote", response_model=QuoteResponse)
async def build_quote(
    req: QuoteRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Build a combined package quote with exchange rate conversion."""
    # Load all referenced packages
    pkg_ids = [item.package_id for item in req.items]
    result = await db.execute(select(Package).where(Package.id.in_(pkg_ids)))
    packages = {p.id: p for p in result.scalars().all()}

    line_items: list[QuoteLineItem] = []
    subtotal = 0.0

    for item in req.items:
        pkg = packages.get(item.package_id)
        if not pkg:
            raise HTTPException(404, f"Package {item.package_id} not found")

        unit_price = item.custom_price if item.custom_price is not None else float(pkg.base_price or 0)
        item_subtotal = unit_price * item.quantity

        line_items.append(
            QuoteLineItem(
                package_name_ja=pkg.name_ja,
                package_name_ko=pkg.name_ko,
                category=pkg.category,
                quantity=item.quantity,
                unit_price=unit_price,
                subtotal=item_subtotal,
                currency=pkg.currency,
            )
        )
        subtotal += item_subtotal

    discount_amount = subtotal * (req.discount_percent / 100)
    total = subtotal - discount_amount

    # Exchange rate conversion
    exchange_rate = None
    total_converted = None
    converted_currency = None

    if req.target_currency == Currency.KRW:
        rate = await get_exchange_rate()
        exchange_rate = rate
        total_converted = round(total * rate, 0)
        converted_currency = Currency.KRW
    elif req.target_currency == Currency.JPY:
        # If packages are in KRW, convert to JPY
        rate = await get_exchange_rate()
        exchange_rate = round(1 / rate, 6)
        total_converted = round(total / rate, 0)
        converted_currency = Currency.JPY

    return QuoteResponse(
        line_items=line_items,
        subtotal=subtotal,
        discount_percent=req.discount_percent,
        discount_amount=round(discount_amount, 2),
        total=round(total, 2),
        target_currency=req.target_currency,
        exchange_rate=exchange_rate,
        total_converted=total_converted,
        converted_currency=converted_currency,
        customer_name=req.customer_name,
        notes=req.notes,
        generated_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# AI Package Recommendation
# ---------------------------------------------------------------------------


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_packages(
    req: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """AI-powered package recommendation based on customer profile."""
    # Load active packages for context
    result = await db.execute(
        select(Package).where(Package.is_active == True).limit(50)
    )
    packages = result.scalars().all()

    if not packages:
        raise HTTPException(404, "No active packages available")

    # Build package catalog for AI
    catalog = "\n".join(
        f"- ID:{p.id} | {p.name_ja} ({p.name_ko}) | "
        f"카테고리:{p.category.value} | "
        f"가격:{p.base_price} {p.currency.value} | "
        f"기간:{p.duration_days}일 | "
        f"포함:{', '.join(p.includes or [])}"
        for p in packages
    )

    # Build customer profile
    profile_parts = []
    if req.customer_tags:
        profile_parts.append(f"관심 태그: {', '.join(req.customer_tags)}")
    if req.budget_jpy:
        profile_parts.append(f"예산: ¥{req.budget_jpy:,.0f}")
    if req.duration_days:
        profile_parts.append(f"희망 기간: {req.duration_days}일")
    if req.interests:
        profile_parts.append(f"관심사: {req.interests}")

    customer_profile = "\n".join(profile_parts) if profile_parts else "정보 없음"

    system_prompt = (
        "あなたはNARUU（ナル）のパッケージコンサルタントAIです。"
        "大邱の美容観光・医療観光パッケージを推薦する専門家です。"
        "顧客のプロフィールと予算に基づいて、最適なパッケージを日本語で推薦してください。"
        "医療効果の保証は絶対にしないでください。"
        "必ず以下の形式で回答してください：\n"
        "1. おすすめ理由の説明\n"
        "2. 推薦パッケージのID一覧（カンマ区切りの数字のみ）を最後の行に "
        "「RECOMMENDED_IDS: 1,2,3」の形式で記載"
    )

    user_message = (
        f"【利用可能なパッケージ一覧】\n{catalog}\n\n"
        f"【顧客プロフィール】\n{customer_profile}\n\n"
        f"この顧客に最適なパッケージを推薦してください。"
    )

    ai = get_ai_service()
    reply = await ai.chat(user_message, system_prompt=system_prompt, max_tokens=1024)

    if not reply:
        raise HTTPException(502, "AI service unavailable")

    # Parse recommended IDs from AI response
    suggested_ids: list[int] = []
    for line in reply.split("\n"):
        if "RECOMMENDED_IDS:" in line:
            ids_part = line.split("RECOMMENDED_IDS:")[-1].strip()
            for token in ids_part.replace(",", " ").split():
                try:
                    suggested_ids.append(int(token.strip()))
                except ValueError:
                    pass
            break

    # Filter to only valid package IDs
    valid_ids = {p.id for p in packages}
    suggested_ids = [i for i in suggested_ids if i in valid_ids]

    # Clean recommendation text (remove the ID line)
    recommendation = "\n".join(
        line for line in reply.split("\n") if "RECOMMENDED_IDS:" not in line
    ).strip()

    return RecommendResponse(
        recommendation=recommendation,
        suggested_package_ids=suggested_ids,
    )
