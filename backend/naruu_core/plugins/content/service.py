"""콘텐츠 CRUD + 파이프라인 서비스."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_core.models.content import Content, ContentSchedule
from naruu_core.plugins.content.pipeline.base import StageHandler
from naruu_core.plugins.content.pipeline.script_generator import ScriptGenerator
from naruu_core.plugins.content.schemas import (
    ContentCreate,
    ContentUpdate,
    ScheduleCreate,
    ScheduleUpdate,
)

logger = logging.getLogger(__name__)

# 파이프라인 단계 순서
PIPELINE_ORDER = [
    "pending", "script", "image", "voice", "video", "publish", "done",
]

# 단계별 AI 핸들러 맵 — 핸들러가 없는 단계는 단순 진행
STAGE_HANDLERS: dict[str, type[StageHandler] | None] = {
    "script": ScriptGenerator,
    "image": None,    # Phase 4: DALL-E
    "voice": None,    # Phase 4: VOICEVOX
    "video": None,    # Phase 4: FFmpeg
    "publish": None,  # Phase 4: YouTube API
}


class ContentCRUD:
    """콘텐츠 CRUD + 파이프라인 오퍼레이션."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- Content --

    async def create_content(self, data: ContentCreate) -> Content:
        """콘텐츠 생성."""
        content = Content(
            title=data.title,
            content_type=data.content_type,
            language=data.language,
            topic=data.topic,
            script=data.script,
        )
        self._session.add(content)
        await self._session.commit()
        await self._session.refresh(content)
        return content

    async def get_content(self, content_id: str) -> Content | None:
        """콘텐츠 단건 조회."""
        result = await self._session.execute(
            select(Content).where(Content.id == content_id)
        )
        return result.scalar_one_or_none()

    async def list_contents(
        self,
        status: str | None = None,
        content_type: str | None = None,
    ) -> list[Content]:
        """콘텐츠 목록."""
        stmt = select(Content).order_by(Content.created_at.desc())
        if status:
            stmt = stmt.where(Content.status == status)
        if content_type:
            stmt = stmt.where(Content.content_type == content_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_content(
        self, content_id: str, data: ContentUpdate
    ) -> Content | None:
        """콘텐츠 수정."""
        content = await self.get_content(content_id)
        if content is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(content, field, value)
        await self._session.commit()
        await self._session.refresh(content)
        return content

    async def advance_pipeline(
        self,
        content_id: str,
        config: dict[str, Any] | None = None,
    ) -> Content | None:
        """파이프라인 다음 단계로 진행.

        현재 단계에 AI 핸들러가 있으면 실행 후 결과에 따라 진행.
        핸들러가 없으면 단순 단계 이동.
        """
        content = await self.get_content(content_id)
        if content is None:
            return None

        current = content.pipeline_stage
        if current not in PIPELINE_ORDER:
            return content

        idx = PIPELINE_ORDER.index(current)
        if idx >= len(PIPELINE_ORDER) - 1:
            return content  # 이미 done

        # 현재 단계에 AI 핸들러가 있는지 확인
        handler_cls = STAGE_HANDLERS.get(current)
        if handler_cls is not None:
            handler = handler_cls()
            result = await handler.execute(content, config or {})

            if result.success:
                content.pipeline_stage = result.next_stage
                content.cost_usd += result.cost_usd
                # 생성된 데이터 반영
                if "script" in result.data:
                    content.script = result.data["script"]
                logger.info(
                    "파이프라인 AI 단계 완료: %s → %s (cost=$%.4f)",
                    current,
                    result.next_stage,
                    result.cost_usd,
                )
            else:
                content.pipeline_stage = "failed"
                content.error_message = result.error
                logger.warning(
                    "파이프라인 AI 단계 실패: %s → failed (%s)",
                    current,
                    result.error,
                )
        else:
            # 핸들러 없는 단계 → 단순 진행
            content.pipeline_stage = PIPELINE_ORDER[idx + 1]

        await self._session.commit()
        await self._session.refresh(content)
        return content

    # -- Schedule --

    async def create_schedule(self, data: ScheduleCreate) -> ContentSchedule:
        """스케줄 생성."""
        schedule = ContentSchedule(
            name=data.name,
            content_type=data.content_type,
            topic_template=data.topic_template,
            language=data.language,
            cron_expression=data.cron_expression,
        )
        self._session.add(schedule)
        await self._session.commit()
        await self._session.refresh(schedule)
        return schedule

    async def get_schedule(self, schedule_id: str) -> ContentSchedule | None:
        """스케줄 조회."""
        result = await self._session.execute(
            select(ContentSchedule).where(ContentSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def list_schedules(
        self, active_only: bool = True
    ) -> list[ContentSchedule]:
        """스케줄 목록."""
        stmt = select(ContentSchedule).order_by(ContentSchedule.name)
        if active_only:
            stmt = stmt.where(ContentSchedule.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_schedule(
        self, schedule_id: str, data: ScheduleUpdate
    ) -> ContentSchedule | None:
        """스케줄 수정."""
        schedule = await self.get_schedule(schedule_id)
        if schedule is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(schedule, field, value)
        await self._session.commit()
        await self._session.refresh(schedule)
        return schedule

    async def delete_schedule(self, schedule_id: str) -> bool:
        """스케줄 삭제."""
        schedule = await self.get_schedule(schedule_id)
        if schedule is None:
            return False
        await self._session.delete(schedule)
        await self._session.commit()
        return True
