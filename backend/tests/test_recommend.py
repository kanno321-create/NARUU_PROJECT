"""관광 추천 엔진 테스트."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from naruu_core.plugins.recommend.plugin import Plugin as RecommendPlugin
from naruu_core.plugins.recommend.schemas import (
    RecommendRequest,
    SpotCreate,
    SpotUpdate,
)
from naruu_core.plugins.recommend.scoring import WEIGHTS, haversine_km, score_spot
from naruu_core.plugins.recommend.service import RecommendCRUD

# ── Unit 테스트: 스팟 스키마 ──


@pytest.mark.unit
class TestSpotSchemas:
    """스팟 스키마 유효성 테스트."""

    def test_spot_create_valid(self) -> None:
        """유효한 스팟 생성."""
        data = SpotCreate(
            name_ja="大邱美容クリニック",
            category="medical",
            rating=4.5,
            avg_price_krw=500000,
        )
        assert data.name_ja == "大邱美容クリニック"
        assert data.category == "medical"
        assert data.rating == 4.5

    def test_spot_create_defaults(self) -> None:
        """기본값으로 스팟 생성."""
        data = SpotCreate(name_ja="Test")
        assert data.category == "tourism"
        assert data.latitude == 0.0
        assert data.avg_price_krw == 0
        assert data.tags == ""

    def test_spot_create_invalid_category(self) -> None:
        """유효하지 않은 카테고리."""
        with pytest.raises(ValidationError):
            SpotCreate(name_ja="Test", category="restaurant")

    def test_spot_create_invalid_rating(self) -> None:
        """범위 초과 평점."""
        with pytest.raises(ValidationError):
            SpotCreate(name_ja="Test", rating=6.0)

    def test_spot_create_invalid_latitude(self) -> None:
        """범위 초과 위도."""
        with pytest.raises(ValidationError):
            SpotCreate(name_ja="Test", latitude=100.0)

    def test_recommend_request_defaults(self) -> None:
        """추천 요청 기본값."""
        req = RecommendRequest()
        assert req.categories == []
        assert req.budget_krw == 0
        assert req.limit == 5

    def test_recommend_request_limit_bounds(self) -> None:
        """추천 요청 limit 범위."""
        with pytest.raises(ValidationError):
            RecommendRequest(limit=0)
        with pytest.raises(ValidationError):
            RecommendRequest(limit=51)


# ── Unit 테스트: 스코어링 엔진 ──


@pytest.mark.unit
class TestScoring:
    """스코어링 엔진 테스트."""

    def test_weights_sum_to_one(self) -> None:
        """가중치 합 = 1.0."""
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_perfect_match(self) -> None:
        """완벽 매치 → 높은 점수."""
        score, reasons = score_spot(
            category="medical",
            tags_csv="整形,二重",
            rating=5.0,
            popularity_score=1.0,
            avg_price_krw=500000,
            req_categories=["medical"],
            req_tags=["整形"],
            req_budget_krw=1000000,
        )
        assert score >= 0.8
        assert any("카테고리" in r for r in reasons)

    def test_no_match(self) -> None:
        """전혀 매치 안 됨 → 낮은 점수."""
        score, reasons = score_spot(
            category="food",
            tags_csv="맛집",
            rating=0.0,
            popularity_score=0.0,
            avg_price_krw=0,
            req_categories=["medical"],
            req_tags=["整形"],
            req_budget_krw=100000,
        )
        assert score < 0.3

    def test_category_match_weight(self) -> None:
        """카테고리 매치 시 점수 증가."""
        matched, _ = score_spot(
            category="beauty",
            tags_csv="",
            rating=3.0,
            popularity_score=0.5,
            avg_price_krw=0,
            req_categories=["beauty"],
            req_tags=[],
            req_budget_krw=0,
        )
        unmatched, _ = score_spot(
            category="food",
            tags_csv="",
            rating=3.0,
            popularity_score=0.5,
            avg_price_krw=0,
            req_categories=["beauty"],
            req_tags=[],
            req_budget_krw=0,
        )
        assert matched > unmatched

    def test_budget_fit(self) -> None:
        """예산 범위 내 → 점수 보너스."""
        within, reasons_in = score_spot(
            category="tourism",
            tags_csv="",
            rating=3.0,
            popularity_score=0.5,
            avg_price_krw=50000,
            req_categories=[],
            req_tags=[],
            req_budget_krw=100000,
        )
        over, reasons_over = score_spot(
            category="tourism",
            tags_csv="",
            rating=3.0,
            popularity_score=0.5,
            avg_price_krw=200000,
            req_categories=[],
            req_tags=[],
            req_budget_krw=100000,
        )
        assert within >= over
        assert any("예산" in r for r in reasons_in)

    def test_tag_matching(self) -> None:
        """태그 매치율 반영."""
        full, _ = score_spot(
            category="tourism",
            tags_csv="温泉,大邱",
            rating=3.0,
            popularity_score=0.5,
            avg_price_krw=0,
            req_categories=[],
            req_tags=["温泉", "大邱"],
            req_budget_krw=0,
        )
        partial, _ = score_spot(
            category="tourism",
            tags_csv="温泉",
            rating=3.0,
            popularity_score=0.5,
            avg_price_krw=0,
            req_categories=[],
            req_tags=["温泉", "大邱"],
            req_budget_krw=0,
        )
        assert full >= partial

    def test_no_filters_neutral(self) -> None:
        """필터 없으면 중간 점수."""
        score, _ = score_spot(
            category="tourism",
            tags_csv="",
            rating=0.0,
            popularity_score=0.0,
            avg_price_krw=0,
            req_categories=[],
            req_tags=[],
            req_budget_krw=0,
        )
        assert 0.2 <= score <= 0.6


# ── Unit 테스트: Haversine ──


@pytest.mark.unit
class TestHaversine:
    """Haversine 거리 계산 테스트."""

    def test_same_point(self) -> None:
        """동일 좌표 → 0km."""
        assert haversine_km(35.87, 128.60, 35.87, 128.60) == 0.0

    def test_daegu_to_seoul(self) -> None:
        """대구~서울 약 240km."""
        dist = haversine_km(35.87, 128.60, 37.57, 127.0)
        assert 230 < dist < 260


# ── Unit 테스트: 플러그인 ──


@pytest.mark.unit
class TestRecommendPlugin:
    """추천 플러그인 인터페이스 테스트."""

    def test_plugin_name(self) -> None:
        plugin = RecommendPlugin()
        assert plugin.name == "recommend"

    def test_plugin_capabilities(self) -> None:
        plugin = RecommendPlugin()
        caps = plugin.capabilities()
        assert "spot.create" in caps
        assert "recommend.search" in caps
        assert len(caps) == 5

    async def test_plugin_execute(self) -> None:
        plugin = RecommendPlugin()
        await plugin.initialize({})
        result = await plugin.execute("recommend.search", {})
        assert result["status"] == "ok"


# ── Integration 테스트: Spot CRUD ──


@pytest.mark.integration
class TestSpotCRUD:
    """스팟 CRUD 통합 테스트."""

    async def test_create_spot(self, db_session: AsyncSession) -> None:
        """스팟 생성."""
        crud = RecommendCRUD(db_session)
        spot = await crud.create_spot(
            SpotCreate(
                name_ja="大邱美容外科",
                category="medical",
                rating=4.5,
                avg_price_krw=1000000,
                tags="整形,二重,大邱",
            )
        )
        assert spot.id is not None
        assert spot.name_ja == "大邱美容外科"
        assert spot.is_active is True

    async def test_get_spot(self, db_session: AsyncSession) -> None:
        """스팟 단건 조회."""
        crud = RecommendCRUD(db_session)
        created = await crud.create_spot(
            SpotCreate(name_ja="テストスポット")
        )
        found = await crud.get_spot(created.id)
        assert found is not None
        assert found.name_ja == "テストスポット"

    async def test_get_nonexistent(self, db_session: AsyncSession) -> None:
        """존재하지 않는 스팟 → None."""
        crud = RecommendCRUD(db_session)
        assert await crud.get_spot("nope") is None

    async def test_list_spots(self, db_session: AsyncSession) -> None:
        """스팟 목록."""
        crud = RecommendCRUD(db_session)
        await crud.create_spot(SpotCreate(name_ja="A", category="medical"))
        await crud.create_spot(SpotCreate(name_ja="B", category="food"))
        await crud.create_spot(SpotCreate(name_ja="C", category="medical"))

        all_items = await crud.list_spots()
        assert len(all_items) == 3

        medical = await crud.list_spots(category="medical")
        assert len(medical) == 2

    async def test_list_active_only(self, db_session: AsyncSession) -> None:
        """활성 스팟만 필터링."""
        crud = RecommendCRUD(db_session)
        await crud.create_spot(SpotCreate(name_ja="Active"))
        s2 = await crud.create_spot(SpotCreate(name_ja="Inactive"))
        await crud.update_spot(s2.id, SpotUpdate(is_active=False))

        active = await crud.list_spots(active_only=True)
        assert len(active) == 1

        all_items = await crud.list_spots(active_only=False)
        assert len(all_items) == 2

    async def test_update_spot(self, db_session: AsyncSession) -> None:
        """스팟 수정."""
        crud = RecommendCRUD(db_session)
        s = await crud.create_spot(
            SpotCreate(name_ja="Old", rating=3.0)
        )
        updated = await crud.update_spot(
            s.id,
            SpotUpdate(name_ja="New", rating=4.8),
        )
        assert updated is not None
        assert updated.name_ja == "New"
        assert updated.rating == 4.8

    async def test_update_nonexistent(
        self, db_session: AsyncSession,
    ) -> None:
        """존재하지 않는 스팟 수정 → None."""
        crud = RecommendCRUD(db_session)
        result = await crud.update_spot(
            "nope", SpotUpdate(name_ja="X")
        )
        assert result is None


# ── Integration 테스트: 추천 검색 ──


@pytest.mark.integration
class TestRecommendSearch:
    """추천 검색 통합 테스트."""

    async def _seed_spots(self, session: AsyncSession) -> None:
        """테스트용 스팟 데이터."""
        crud = RecommendCRUD(session)
        await crud.create_spot(SpotCreate(
            name_ja="大邱美容外科",
            category="medical",
            rating=4.8,
            popularity_score=0.9,
            avg_price_krw=1000000,
            tags="整形,二重,大邱",
        ))
        await crud.create_spot(SpotCreate(
            name_ja="東城路グルメ街",
            category="food",
            rating=4.2,
            popularity_score=0.7,
            avg_price_krw=30000,
            tags="グルメ,大邱,韓国料理",
        ))
        await crud.create_spot(SpotCreate(
            name_ja="八公山ケーブルカー",
            category="tourism",
            rating=4.0,
            popularity_score=0.6,
            avg_price_krw=15000,
            tags="観光,自然,大邱",
        ))

    async def test_recommend_all(self, db_session: AsyncSession) -> None:
        """전체 추천 (필터 없이)."""
        await self._seed_spots(db_session)
        crud = RecommendCRUD(db_session)
        results = await crud.recommend(RecommendRequest(limit=10))
        assert len(results) == 3
        # 점수 내림차순
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    async def test_recommend_category_filter(
        self, db_session: AsyncSession,
    ) -> None:
        """카테고리 필터 → 해당 카테고리 우선."""
        await self._seed_spots(db_session)
        crud = RecommendCRUD(db_session)
        results = await crud.recommend(
            RecommendRequest(categories=["medical"], limit=3)
        )
        assert results[0].spot.category == "medical"

    async def test_recommend_budget_filter(
        self, db_session: AsyncSession,
    ) -> None:
        """예산 필터 → 예산 내 항목 우선."""
        await self._seed_spots(db_session)
        crud = RecommendCRUD(db_session)
        results = await crud.recommend(
            RecommendRequest(budget_krw=50000, limit=3)
        )
        # 저예산 스팟이 상위
        assert results[0].spot.avg_price_krw <= 50000

    async def test_recommend_limit(self, db_session: AsyncSession) -> None:
        """limit 적용."""
        await self._seed_spots(db_session)
        crud = RecommendCRUD(db_session)
        results = await crud.recommend(RecommendRequest(limit=1))
        assert len(results) == 1

    async def test_recommend_empty_db(
        self, db_session: AsyncSession,
    ) -> None:
        """빈 DB → 빈 결과."""
        crud = RecommendCRUD(db_session)
        results = await crud.recommend(RecommendRequest())
        assert results == []


# ── Smoke 테스트 ──


@pytest.mark.smoke
class TestRecommendSmoke:
    """추천 스모크 테스트."""

    async def test_spots_table_exists(
        self, db_engine: AsyncEngine,
    ) -> None:
        """spots 테이블 존재."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='spots'"
                )
            )
            assert result.scalar() == "spots"
