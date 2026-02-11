"""관광 추천 라우터 — 스팟 CRUD + 추천 검색."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_api.deps import get_db_session
from naruu_core.auth.middleware import get_current_user
from naruu_core.plugins.recommend.schemas import (
    RecommendedSpot,
    RecommendRequest,
    SpotCreate,
    SpotResponse,
    SpotUpdate,
)
from naruu_core.plugins.recommend.service import RecommendCRUD

router = APIRouter(prefix="/recommend", tags=["recommend"])


def _spot_resp(s: object) -> SpotResponse:
    return SpotResponse(
        id=s.id,  # type: ignore[attr-defined]
        name_ja=s.name_ja,  # type: ignore[attr-defined]
        name_ko=s.name_ko,  # type: ignore[attr-defined]
        category=s.category,  # type: ignore[attr-defined]
        description_ja=s.description_ja,  # type: ignore[attr-defined]
        address=s.address,  # type: ignore[attr-defined]
        latitude=s.latitude,  # type: ignore[attr-defined]
        longitude=s.longitude,  # type: ignore[attr-defined]
        avg_price_krw=s.avg_price_krw,  # type: ignore[attr-defined]
        rating=s.rating,  # type: ignore[attr-defined]
        popularity_score=s.popularity_score,  # type: ignore[attr-defined]
        tags=s.tags,  # type: ignore[attr-defined]
        is_active=s.is_active,  # type: ignore[attr-defined]
        partner_id=s.partner_id,  # type: ignore[attr-defined]
    )


# -- Spot CRUD --


@router.post("/spots", response_model=SpotResponse, status_code=201)
async def create_spot(
    req: SpotCreate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SpotResponse:
    """스팟 생성."""
    crud = RecommendCRUD(session)
    spot = await crud.create_spot(req)
    return _spot_resp(spot)


@router.get("/spots", response_model=list[SpotResponse])
async def list_spots(
    category: str | None = None,
    active_only: bool = True,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[SpotResponse]:
    """스팟 목록."""
    crud = RecommendCRUD(session)
    items = await crud.list_spots(category=category, active_only=active_only)
    return [_spot_resp(s) for s in items]


@router.get("/spots/{spot_id}", response_model=SpotResponse)
async def get_spot(
    spot_id: str,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SpotResponse:
    """스팟 상세."""
    crud = RecommendCRUD(session)
    spot = await crud.get_spot(spot_id)
    if spot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스팟을 찾을 수 없습니다.",
        )
    return _spot_resp(spot)


@router.patch("/spots/{spot_id}", response_model=SpotResponse)
async def update_spot(
    spot_id: str,
    req: SpotUpdate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SpotResponse:
    """스팟 수정."""
    crud = RecommendCRUD(session)
    spot = await crud.update_spot(spot_id, req)
    if spot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스팟을 찾을 수 없습니다.",
        )
    return _spot_resp(spot)


# -- Recommendation --


@router.post("/search", response_model=list[RecommendedSpot])
async def search_recommendations(
    req: RecommendRequest,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[RecommendedSpot]:
    """추천 검색 — 스코어링 기반."""
    crud = RecommendCRUD(session)
    return await crud.recommend(req)
