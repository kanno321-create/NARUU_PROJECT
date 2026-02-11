"""콘텐츠 자동화 플러그인 테스트."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from naruu_core.plugins.content.plugin import Plugin as ContentPlugin
from naruu_core.plugins.content.schemas import (
    ContentCreate,
    ContentUpdate,
    ScheduleCreate,
    ScheduleUpdate,
)
from naruu_core.plugins.content.service import PIPELINE_ORDER, ContentCRUD

# ── Unit 테스트: 콘텐츠 스키마 ──


@pytest.mark.unit
class TestContentSchemas:
    """콘텐츠 스키마 유효성 테스트."""

    def test_content_create_valid(self) -> None:
        """유효한 콘텐츠 생성."""
        data = ContentCreate(
            title="日本語動画テスト",
            content_type="video",
            language="ja",
            topic="大邱の美容クリニック紹介",
        )
        assert data.title == "日本語動画テスト"
        assert data.content_type == "video"
        assert data.language == "ja"

    def test_content_create_defaults(self) -> None:
        """기본값으로 콘텐츠 생성."""
        data = ContentCreate(title="Test")
        assert data.content_type == "video"
        assert data.language == "ja"
        assert data.topic == ""
        assert data.script == ""

    def test_content_create_invalid_type(self) -> None:
        """유효하지 않은 콘텐츠 타입."""
        with pytest.raises(ValidationError):
            ContentCreate(title="Test", content_type="podcast")

    def test_content_create_invalid_language(self) -> None:
        """유효하지 않은 언어 코드."""
        with pytest.raises(ValidationError):
            ContentCreate(title="Test", language="zh")

    def test_content_create_empty_title(self) -> None:
        """빈 제목 → 에러."""
        with pytest.raises(ValidationError):
            ContentCreate(title="")

    def test_content_update_valid_status(self) -> None:
        """유효한 상태 업데이트."""
        for s in ("draft", "scripted", "produced", "published", "archived"):
            data = ContentUpdate(status=s)
            assert data.status == s

    def test_content_update_invalid_status(self) -> None:
        """유효하지 않은 상태."""
        with pytest.raises(ValidationError):
            ContentUpdate(status="unknown")

    def test_content_update_valid_pipeline(self) -> None:
        """유효한 파이프라인 단계."""
        for stage in ("pending", "script", "image", "voice",
                      "video", "publish", "done", "failed"):
            data = ContentUpdate(pipeline_stage=stage)
            assert data.pipeline_stage == stage

    def test_content_update_invalid_pipeline(self) -> None:
        """유효하지 않은 파이프라인 단계."""
        with pytest.raises(ValidationError):
            ContentUpdate(pipeline_stage="unknown")

    def test_schedule_create_valid(self) -> None:
        """유효한 스케줄 생성."""
        data = ScheduleCreate(
            name="주간 동영상",
            content_type="video",
            topic_template="大邱{category}紹介",
            cron_expression="0 9 * * 1",
        )
        assert data.name == "주간 동영상"
        assert data.cron_expression == "0 9 * * 1"

    def test_schedule_update_active(self) -> None:
        """스케줄 활성/비활성 전환."""
        data = ScheduleUpdate(is_active=False)
        assert data.is_active is False


# ── Unit 테스트: 콘텐츠 플러그인 ──


@pytest.mark.unit
class TestContentPlugin:
    """콘텐츠 플러그인 인터페이스 테스트."""

    def test_plugin_name(self) -> None:
        plugin = ContentPlugin()
        assert plugin.name == "content"

    def test_plugin_version(self) -> None:
        plugin = ContentPlugin()
        assert plugin.version == "0.1.0"

    def test_plugin_capabilities(self) -> None:
        plugin = ContentPlugin()
        caps = plugin.capabilities()
        assert "content.create" in caps
        assert "content.advance_pipeline" in caps
        assert "schedule.create" in caps
        assert len(caps) == 10

    async def test_plugin_execute(self) -> None:
        plugin = ContentPlugin()
        await plugin.initialize({})
        result = await plugin.execute("content.create", {})
        assert result["status"] == "ok"
        assert result["plugin"] == "content"

    async def test_plugin_shutdown(self) -> None:
        plugin = ContentPlugin()
        await plugin.initialize({})
        await plugin.shutdown()


# ── Unit 테스트: 파이프라인 순서 ──


@pytest.mark.unit
class TestPipelineOrder:
    """파이프라인 단계 순서 검증."""

    def test_pipeline_order_length(self) -> None:
        assert len(PIPELINE_ORDER) == 7

    def test_pipeline_starts_pending(self) -> None:
        assert PIPELINE_ORDER[0] == "pending"

    def test_pipeline_ends_done(self) -> None:
        assert PIPELINE_ORDER[-1] == "done"

    def test_pipeline_contains_all_stages(self) -> None:
        expected = {"pending", "script", "image", "voice",
                    "video", "publish", "done"}
        assert set(PIPELINE_ORDER) == expected


# ── Integration 테스트: Content CRUD ──


@pytest.mark.integration
class TestContentCRUD:
    """콘텐츠 CRUD 통합 테스트."""

    async def test_create_content(self, db_session: AsyncSession) -> None:
        """콘텐츠 생성."""
        crud = ContentCRUD(db_session)
        content = await crud.create_content(
            ContentCreate(
                title="大邱美容クリニック紹介動画",
                content_type="video",
                language="ja",
                topic="大邱の美容クリニック",
            )
        )
        assert content.id is not None
        assert content.title == "大邱美容クリニック紹介動画"
        assert content.status == "draft"
        assert content.pipeline_stage == "pending"
        assert content.cost_usd == 0.0

    async def test_get_content(self, db_session: AsyncSession) -> None:
        """콘텐츠 단건 조회."""
        crud = ContentCRUD(db_session)
        created = await crud.create_content(
            ContentCreate(title="테스트 콘텐츠")
        )
        found = await crud.get_content(created.id)
        assert found is not None
        assert found.title == "테스트 콘텐츠"

    async def test_get_nonexistent_content(
        self, db_session: AsyncSession,
    ) -> None:
        """존재하지 않는 콘텐츠 → None."""
        crud = ContentCRUD(db_session)
        assert await crud.get_content("nonexistent") is None

    async def test_list_contents(self, db_session: AsyncSession) -> None:
        """콘텐츠 목록 조회."""
        crud = ContentCRUD(db_session)
        await crud.create_content(ContentCreate(title="A"))
        await crud.create_content(ContentCreate(title="B"))
        await crud.create_content(ContentCreate(title="C"))
        items = await crud.list_contents()
        assert len(items) == 3

    async def test_list_contents_filter_status(
        self, db_session: AsyncSession,
    ) -> None:
        """상태별 필터링."""
        crud = ContentCRUD(db_session)
        c = await crud.create_content(ContentCreate(title="A"))
        await crud.update_content(
            c.id, ContentUpdate(status="published")
        )
        await crud.create_content(ContentCreate(title="B"))

        published = await crud.list_contents(status="published")
        assert len(published) == 1
        assert published[0].title == "A"

    async def test_list_contents_filter_type(
        self, db_session: AsyncSession,
    ) -> None:
        """콘텐츠 타입별 필터링."""
        crud = ContentCRUD(db_session)
        await crud.create_content(
            ContentCreate(title="Video", content_type="video")
        )
        await crud.create_content(
            ContentCreate(title="Blog", content_type="blog")
        )
        videos = await crud.list_contents(content_type="video")
        assert len(videos) == 1
        assert videos[0].title == "Video"

    async def test_update_content(self, db_session: AsyncSession) -> None:
        """콘텐츠 수정."""
        crud = ContentCRUD(db_session)
        c = await crud.create_content(ContentCreate(title="Old"))
        updated = await crud.update_content(
            c.id,
            ContentUpdate(
                title="New",
                status="scripted",
                cost_usd=0.35,
            ),
        )
        assert updated is not None
        assert updated.title == "New"
        assert updated.status == "scripted"
        assert updated.cost_usd == 0.35

    async def test_update_nonexistent_content(
        self, db_session: AsyncSession,
    ) -> None:
        """존재하지 않는 콘텐츠 수정 → None."""
        crud = ContentCRUD(db_session)
        result = await crud.update_content(
            "nope", ContentUpdate(title="X")
        )
        assert result is None


# ── Integration 테스트: 파이프라인 진행 ──


@pytest.mark.integration
class TestPipelineAdvance:
    """파이프라인 단계 진행 테스트."""

    async def test_advance_full_pipeline(
        self, db_session: AsyncSession,
    ) -> None:
        """전체 파이프라인 순서대로 진행."""
        crud = ContentCRUD(db_session)
        c = await crud.create_content(ContentCreate(title="Pipeline Test"))
        assert c.pipeline_stage == "pending"

        for expected_next in PIPELINE_ORDER[1:]:
            c = await crud.advance_pipeline(c.id)
            assert c is not None
            assert c.pipeline_stage == expected_next

    async def test_advance_at_done_stays_done(
        self, db_session: AsyncSession,
    ) -> None:
        """done 단계에서 더 이상 진행 불가."""
        crud = ContentCRUD(db_session)
        c = await crud.create_content(ContentCreate(title="Done Test"))
        # pending → script → image → voice → video → publish → done
        for _ in range(6):
            c = await crud.advance_pipeline(c.id)
        assert c is not None
        assert c.pipeline_stage == "done"

        # done에서 한번 더 → 여전히 done
        c = await crud.advance_pipeline(c.id)
        assert c is not None
        assert c.pipeline_stage == "done"

    async def test_advance_nonexistent(
        self, db_session: AsyncSession,
    ) -> None:
        """존재하지 않는 콘텐츠 파이프라인 → None."""
        crud = ContentCRUD(db_session)
        assert await crud.advance_pipeline("nope") is None


# ── Integration 테스트: Schedule CRUD ──


@pytest.mark.integration
class TestScheduleCRUD:
    """스케줄 CRUD 통합 테스트."""

    async def test_create_schedule(self, db_session: AsyncSession) -> None:
        """스케줄 생성."""
        crud = ContentCRUD(db_session)
        s = await crud.create_schedule(
            ScheduleCreate(
                name="주간 동영상",
                content_type="video",
                topic_template="大邱{category}紹介",
                cron_expression="0 9 * * 1",
            )
        )
        assert s.id is not None
        assert s.name == "주간 동영상"
        assert s.is_active is True
        assert s.last_run_at is None

    async def test_list_schedules_active_only(
        self, db_session: AsyncSession,
    ) -> None:
        """활성 스케줄만 목록."""
        crud = ContentCRUD(db_session)
        await crud.create_schedule(ScheduleCreate(name="Active"))
        s2 = await crud.create_schedule(ScheduleCreate(name="Inactive"))
        await crud.update_schedule(
            s2.id, ScheduleUpdate(is_active=False)
        )

        active = await crud.list_schedules(active_only=True)
        assert len(active) == 1
        assert active[0].name == "Active"

        all_items = await crud.list_schedules(active_only=False)
        assert len(all_items) == 2

    async def test_update_schedule(self, db_session: AsyncSession) -> None:
        """스케줄 수정."""
        crud = ContentCRUD(db_session)
        s = await crud.create_schedule(ScheduleCreate(name="Old"))
        updated = await crud.update_schedule(
            s.id, ScheduleUpdate(name="New", cron_expression="0 10 * * *")
        )
        assert updated is not None
        assert updated.name == "New"
        assert updated.cron_expression == "0 10 * * *"

    async def test_update_nonexistent_schedule(
        self, db_session: AsyncSession,
    ) -> None:
        """존재하지 않는 스케줄 수정 → None."""
        crud = ContentCRUD(db_session)
        result = await crud.update_schedule(
            "nope", ScheduleUpdate(name="X")
        )
        assert result is None

    async def test_delete_schedule(self, db_session: AsyncSession) -> None:
        """스케줄 삭제."""
        crud = ContentCRUD(db_session)
        s = await crud.create_schedule(ScheduleCreate(name="ToDelete"))
        assert await crud.delete_schedule(s.id) is True
        assert await crud.get_schedule(s.id) is None

    async def test_delete_nonexistent_schedule(
        self, db_session: AsyncSession,
    ) -> None:
        """존재하지 않는 스케줄 삭제 → False."""
        crud = ContentCRUD(db_session)
        assert await crud.delete_schedule("nope") is False


# ── Smoke 테스트 ──


@pytest.mark.smoke
class TestContentSmoke:
    """콘텐츠 스모크 테스트."""

    async def test_contents_table_exists(
        self, db_engine: AsyncEngine,
    ) -> None:
        """contents 테이블 존재."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='contents'"
                )
            )
            assert result.scalar() == "contents"

    async def test_content_schedules_table_exists(
        self, db_engine: AsyncEngine,
    ) -> None:
        """content_schedules 테이블 존재."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='content_schedules'"
                )
            )
            assert result.scalar() == "content_schedules"
