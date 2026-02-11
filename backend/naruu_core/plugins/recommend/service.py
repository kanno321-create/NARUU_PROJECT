"""관광 추천 CRUD + 스코어링 서비스."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_core.models.recommendation import Spot
from naruu_core.plugins.recommend.schemas import (
    RecommendedSpot,
    RecommendRequest,
    SpotCreate,
    SpotResponse,
    SpotUpdate,
)
from naruu_core.plugins.recommend.scoring import score_spot


class RecommendCRUD:
    """관광 스팟 CRUD + 추천 오퍼레이션."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- Spot CRUD --

    async def create_spot(self, data: SpotCreate) -> Spot:
        """스팟 생성."""
        spot = Spot(
            name_ja=data.name_ja,
            name_ko=data.name_ko,
            category=data.category,
            description_ja=data.description_ja,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            avg_price_krw=data.avg_price_krw,
            rating=data.rating,
            tags=data.tags,
            partner_id=data.partner_id,
        )
        self._session.add(spot)
        await self._session.commit()
        await self._session.refresh(spot)
        return spot

    async def get_spot(self, spot_id: str) -> Spot | None:
        """스팟 단건 조회."""
        result = await self._session.execute(
            select(Spot).where(Spot.id == spot_id)
        )
        return result.scalar_one_or_none()

    async def list_spots(
        self,
        category: str | None = None,
        active_only: bool = True,
    ) -> list[Spot]:
        """스팟 목록."""
        stmt = select(Spot).order_by(Spot.name_ja)
        if active_only:
            stmt = stmt.where(Spot.is_active.is_(True))
        if category:
            stmt = stmt.where(Spot.category == category)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_spot(
        self, spot_id: str, data: SpotUpdate,
    ) -> Spot | None:
        """스팟 수정."""
        spot = await self.get_spot(spot_id)
        if spot is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(spot, field, value)
        await self._session.commit()
        await self._session.refresh(spot)
        return spot

    # -- Recommendation --

    async def recommend(
        self, req: RecommendRequest,
    ) -> list[RecommendedSpot]:
        """추천 스팟 조회 (스코어링 기반)."""
        spots = await self.list_spots(active_only=True)

        scored: list[tuple[float, Spot, list[str]]] = []
        for spot in spots:
            total, reasons = score_spot(
                category=spot.category,
                tags_csv=spot.tags,
                rating=spot.rating,
                popularity_score=spot.popularity_score,
                avg_price_krw=spot.avg_price_krw,
                req_categories=req.categories,
                req_tags=req.tags,
                req_budget_krw=req.budget_krw,
            )
            scored.append((total, spot, reasons))

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[RecommendedSpot] = []
        for total, spot, reasons in scored[: req.limit]:
            results.append(
                RecommendedSpot(
                    spot=SpotResponse(
                        id=spot.id,
                        name_ja=spot.name_ja,
                        name_ko=spot.name_ko,
                        category=spot.category,
                        description_ja=spot.description_ja,
                        address=spot.address,
                        latitude=spot.latitude,
                        longitude=spot.longitude,
                        avg_price_krw=spot.avg_price_krw,
                        rating=spot.rating,
                        popularity_score=spot.popularity_score,
                        tags=spot.tags,
                        is_active=spot.is_active,
                        partner_id=spot.partner_id,
                    ),
                    score=total,
                    reasons=reasons,
                )
            )
        return results
