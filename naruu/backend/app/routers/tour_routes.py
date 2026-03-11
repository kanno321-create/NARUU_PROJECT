"""Tour route management: CRUD, Google Maps directions, AI route suggestion."""

from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.tour_route import RouteStatus, TourRoute
from app.models.partner import Partner
from app.models.user import User
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/tour-routes", tags=["tour-routes"])
settings = get_settings()

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class WaypointIn(BaseModel):
    order: int
    place_id: str | None = None
    name_ja: str
    name_ko: str
    lat: float
    lng: float
    category: str = "tourism"  # tourism|medical|restaurant|hotel|shopping
    stay_minutes: int = 60
    notes: str | None = None
    partner_id: int | None = None


class RouteCreate(BaseModel):
    name_ja: str = Field(..., min_length=1, max_length=200)
    name_ko: str = Field(..., min_length=1, max_length=200)
    description_ja: str | None = None
    description_ko: str | None = None
    waypoints: list[WaypointIn] = []
    tags: list[str] | None = None
    is_template: bool = False
    customer_id: int | None = None
    package_id: int | None = None


class RouteUpdate(BaseModel):
    name_ja: str | None = None
    name_ko: str | None = None
    description_ja: str | None = None
    description_ko: str | None = None
    waypoints: list[WaypointIn] | None = None
    status: RouteStatus | None = None
    tags: list[str] | None = None
    is_template: bool | None = None
    customer_id: int | None = None
    package_id: int | None = None


class RouteOut(BaseModel):
    id: int
    name_ja: str
    name_ko: str
    description_ja: str | None = None
    description_ko: str | None = None
    waypoints: list | None = None
    route_data: dict | None = None
    status: RouteStatus
    total_duration_minutes: int | None = None
    total_distance_km: float | None = None
    tags: list[str] | None = None
    is_template: bool
    customer_id: int | None = None
    package_id: int | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RouteListResponse(BaseModel):
    items: list[RouteOut]
    total: int
    page: int
    per_page: int


# --- Google Maps Proxy Schemas ---


class DirectionsRequest(BaseModel):
    origin: dict  # {"lat": ..., "lng": ...}
    destination: dict
    waypoints: list[dict] = []  # [{"lat": ..., "lng": ...}, ...]
    optimize: bool = True
    mode: str = "driving"  # driving|walking|transit


class PlaceSearchRequest(BaseModel):
    query: str
    lat: float = 35.8714  # Daegu center default
    lng: float = 128.5964
    radius: int = 5000
    type: str | None = None  # restaurant, hospital, tourist_attraction, etc.


class DistanceMatrixRequest(BaseModel):
    origins: list[dict]  # [{"lat": ..., "lng": ...}]
    destinations: list[dict]
    mode: str = "driving"


# --- AI Route Suggestion ---


class RouteSuggestRequest(BaseModel):
    customer_tags: list[str] | None = None
    duration_days: int = 1
    interests: str | None = None
    include_medical: bool = False
    budget_level: str = "medium"  # low|medium|high


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=RouteListResponse)
async def list_routes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: RouteStatus | None = None,
    template_only: bool = False,
    customer_id: int | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(TourRoute)

    if status:
        q = q.where(TourRoute.status == status)
    if template_only:
        q = q.where(TourRoute.is_template == True)
    if customer_id:
        q = q.where(TourRoute.customer_id == customer_id)
    if search:
        pattern = f"%{search}%"
        q = q.where(
            (TourRoute.name_ja.ilike(pattern)) | (TourRoute.name_ko.ilike(pattern))
        )

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(TourRoute.created_at.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    return RouteListResponse(
        items=[RouteOut.model_validate(r) for r in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{route_id}", response_model=RouteOut)
async def get_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(TourRoute).where(TourRoute.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(404, "Route not found")
    return RouteOut.model_validate(route)


@router.post("", response_model=RouteOut, status_code=201)
async def create_route(
    data: RouteCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    route = TourRoute(
        name_ja=data.name_ja,
        name_ko=data.name_ko,
        description_ja=data.description_ja,
        description_ko=data.description_ko,
        waypoints=[w.model_dump() for w in data.waypoints],
        status=RouteStatus.DRAFT,
        tags=data.tags,
        is_template=data.is_template,
        customer_id=data.customer_id,
        package_id=data.package_id,
        created_by=user.id,
    )
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return RouteOut.model_validate(route)


@router.put("/{route_id}", response_model=RouteOut)
async def update_route(
    route_id: int,
    data: RouteUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(TourRoute).where(TourRoute.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(404, "Route not found")

    update_data = data.model_dump(exclude_unset=True)
    if "waypoints" in update_data and update_data["waypoints"] is not None:
        update_data["waypoints"] = [
            w.model_dump() if hasattr(w, "model_dump") else w
            for w in update_data["waypoints"]
        ]

    for key, value in update_data.items():
        setattr(route, key, value)

    await db.commit()
    await db.refresh(route)
    return RouteOut.model_validate(route)


@router.delete("/{route_id}")
async def delete_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(TourRoute).where(TourRoute.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(404, "Route not found")

    route.status = RouteStatus.ARCHIVED
    await db.commit()
    return {"message": "Route archived"}


# ---------------------------------------------------------------------------
# Google Maps Proxy Endpoints
# ---------------------------------------------------------------------------


@router.post("/directions")
async def get_directions(
    req: DirectionsRequest,
    _user: User = Depends(get_current_user),
):
    """Proxy to Google Directions API — calculates route between waypoints."""
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(503, "Google Maps API key not configured")

    params: dict = {
        "origin": f"{req.origin['lat']},{req.origin['lng']}",
        "destination": f"{req.destination['lat']},{req.destination['lng']}",
        "mode": req.mode,
        "language": "ja",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }

    if req.waypoints:
        wp_str = "|".join(f"{w['lat']},{w['lng']}" for w in req.waypoints)
        if req.optimize:
            wp_str = f"optimize:true|{wp_str}"
        params["waypoints"] = wp_str

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params=params,
        )
        data = resp.json()

    if data.get("status") != "OK":
        raise HTTPException(502, f"Directions API error: {data.get('status')}")

    # Parse response into simplified format
    route = data["routes"][0]
    legs = []
    total_distance = 0
    total_duration = 0

    for leg in route["legs"]:
        distance_km = leg["distance"]["value"] / 1000
        duration_min = leg["duration"]["value"] / 60
        total_distance += distance_km
        total_duration += duration_min
        legs.append({
            "from": leg["start_address"],
            "to": leg["end_address"],
            "distance_km": round(distance_km, 1),
            "duration_minutes": round(duration_min),
            "polyline": leg.get("steps", [{}])[0].get("polyline", {}).get("points", ""),
        })

    return {
        "total_distance_km": round(total_distance, 1),
        "total_duration_minutes": round(total_duration),
        "legs": legs,
        "overview_polyline": route.get("overview_polyline", {}).get("points", ""),
        "waypoint_order": route.get("waypoint_order", []),
    }


@router.post("/places/search")
async def search_places(
    req: PlaceSearchRequest,
    _user: User = Depends(get_current_user),
):
    """Search nearby places using Google Places API."""
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(503, "Google Maps API key not configured")

    params = {
        "query": req.query,
        "location": f"{req.lat},{req.lng}",
        "radius": req.radius,
        "language": "ja",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }
    if req.type:
        params["type"] = req.type

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params,
        )
        data = resp.json()

    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise HTTPException(502, f"Places API error: {data.get('status')}")

    places = []
    for p in data.get("results", [])[:20]:
        loc = p.get("geometry", {}).get("location", {})
        places.append({
            "place_id": p.get("place_id"),
            "name": p.get("name"),
            "address": p.get("formatted_address"),
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "rating": p.get("rating"),
            "types": p.get("types", []),
            "photo_reference": (
                p["photos"][0]["photo_reference"]
                if p.get("photos")
                else None
            ),
        })

    return {"places": places, "total": len(places)}


@router.post("/distance-matrix")
async def get_distance_matrix(
    req: DistanceMatrixRequest,
    _user: User = Depends(get_current_user),
):
    """Calculate travel times between multiple points."""
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(503, "Google Maps API key not configured")

    origins = "|".join(f"{o['lat']},{o['lng']}" for o in req.origins)
    destinations = "|".join(f"{d['lat']},{d['lng']}" for d in req.destinations)

    params = {
        "origins": origins,
        "destinations": destinations,
        "mode": req.mode,
        "language": "ja",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params=params,
        )
        data = resp.json()

    if data.get("status") != "OK":
        raise HTTPException(502, f"Distance Matrix API error: {data.get('status')}")

    return data


# ---------------------------------------------------------------------------
# Calculate & Cache Route Data
# ---------------------------------------------------------------------------


@router.post("/{route_id}/calculate", response_model=RouteOut)
async def calculate_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Calculate directions for a saved route and cache the results."""
    result = await db.execute(select(TourRoute).where(TourRoute.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(404, "Route not found")

    waypoints = route.waypoints or []
    if len(waypoints) < 2:
        raise HTTPException(400, "At least 2 waypoints needed")

    # Sort by order
    sorted_wp = sorted(waypoints, key=lambda w: w.get("order", 0))

    origin = {"lat": sorted_wp[0]["lat"], "lng": sorted_wp[0]["lng"]}
    destination = {"lat": sorted_wp[-1]["lat"], "lng": sorted_wp[-1]["lng"]}
    intermediate = [
        {"lat": w["lat"], "lng": w["lng"]} for w in sorted_wp[1:-1]
    ]

    # Call directions
    directions_req = DirectionsRequest(
        origin=origin,
        destination=destination,
        waypoints=intermediate,
        optimize=True,
    )
    directions = await get_directions(directions_req, _user)

    # Add stay times to total duration
    total_stay = sum(w.get("stay_minutes", 0) for w in sorted_wp)
    total_with_stay = directions["total_duration_minutes"] + total_stay

    route.route_data = directions
    route.total_distance_km = directions["total_distance_km"]
    route.total_duration_minutes = total_with_stay

    await db.commit()
    await db.refresh(route)
    return RouteOut.model_validate(route)


# ---------------------------------------------------------------------------
# AI Route Suggestion
# ---------------------------------------------------------------------------


@router.post("/suggest")
async def suggest_route(
    req: RouteSuggestRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """AI-powered route suggestion based on customer preferences."""
    # Load active partners for context
    partner_result = await db.execute(
        select(Partner).where(Partner.is_active == True).limit(30)
    )
    partners = partner_result.scalars().all()

    partner_catalog = "\n".join(
        f"- {p.name_ja or p.name_ko} ({p.type.value}) | 주소: {p.address or '미정'}"
        for p in partners
    ) or "등록된 제휴업체 없음"

    # Load template routes for reference
    template_result = await db.execute(
        select(TourRoute).where(TourRoute.is_template == True).limit(10)
    )
    templates = template_result.scalars().all()

    template_info = "\n".join(
        f"- {t.name_ja}: {len(t.waypoints or [])}곳, {t.total_duration_minutes or '?'}분"
        for t in templates
    ) or "템플릿 루트 없음"

    profile_parts = []
    if req.customer_tags:
        profile_parts.append(f"태그: {', '.join(req.customer_tags)}")
    if req.interests:
        profile_parts.append(f"관심사: {req.interests}")
    profile_parts.append(f"일정: {req.duration_days}일")
    profile_parts.append(f"예산: {req.budget_level}")
    if req.include_medical:
        profile_parts.append("의료관광 포함 희망")

    system_prompt = (
        "あなたはNARUU（ナル）の大邱観光ルートプランナーAIです。"
        "大邱の人気観光スポット、グルメ、ショッピング、医療施設に精通しています。"
        "顧客の希望に合わせた最適な観光ルートを日本語で提案してください。"
        "各スポットには以下の情報を含めてください：\n"
        "- スポット名（日本語・韓国語）\n"
        "- カテゴリ（観光/グルメ/ショッピング/医療）\n"
        "- おすすめ滞在時間\n"
        "- 一言コメント\n\n"
        "医療効果の保証は絶対にしないでください。"
    )

    user_message = (
        f"【提携先一覧】\n{partner_catalog}\n\n"
        f"【テンプレートルート】\n{template_info}\n\n"
        f"【顧客プロフィール】\n{chr(10).join(profile_parts)}\n\n"
        f"{req.duration_days}日間の大邱観光ルートを提案してください。"
    )

    ai = get_ai_service()
    reply = await ai.chat(user_message, system_prompt=system_prompt, max_tokens=1500)

    if not reply:
        raise HTTPException(502, "AI service unavailable")

    return {"suggestion": reply}


# ---------------------------------------------------------------------------
# Google Maps API Key (for frontend)
# ---------------------------------------------------------------------------


@router.get("/maps-config")
async def maps_config(_user: User = Depends(get_current_user)):
    """Return Google Maps API key for frontend use."""
    if not settings.GOOGLE_MAPS_API_KEY:
        return {"api_key": None, "configured": False}
    return {"api_key": settings.GOOGLE_MAPS_API_KEY, "configured": True}
