"""콘텐츠 관리 라우터 — 콘텐츠 CRUD + 파이프라인 + 스케줄."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_api.deps import get_db_session
from naruu_core.auth.middleware import get_current_user
from naruu_core.plugins.content.schemas import (
    ContentCreate,
    ContentResponse,
    ContentUpdate,
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from naruu_core.plugins.content.service import ContentCRUD

router = APIRouter(prefix="/content", tags=["content"])


def _content_resp(c: object) -> ContentResponse:
    return ContentResponse(
        id=c.id,  # type: ignore[attr-defined]
        title=c.title,  # type: ignore[attr-defined]
        content_type=c.content_type,  # type: ignore[attr-defined]
        language=c.language,  # type: ignore[attr-defined]
        topic=c.topic,  # type: ignore[attr-defined]
        script=c.script,  # type: ignore[attr-defined]
        status=c.status,  # type: ignore[attr-defined]
        pipeline_stage=c.pipeline_stage,  # type: ignore[attr-defined]
        cost_usd=c.cost_usd,  # type: ignore[attr-defined]
        publish_url=c.publish_url,  # type: ignore[attr-defined]
        error_message=c.error_message,  # type: ignore[attr-defined]
    )


def _schedule_resp(s: object) -> ScheduleResponse:
    return ScheduleResponse(
        id=s.id,  # type: ignore[attr-defined]
        name=s.name,  # type: ignore[attr-defined]
        content_type=s.content_type,  # type: ignore[attr-defined]
        topic_template=s.topic_template,  # type: ignore[attr-defined]
        language=s.language,  # type: ignore[attr-defined]
        cron_expression=s.cron_expression,  # type: ignore[attr-defined]
        is_active=s.is_active,  # type: ignore[attr-defined]
        last_run_at=s.last_run_at,  # type: ignore[attr-defined]
    )


# -- Content --


@router.post("", response_model=ContentResponse, status_code=201)
async def create_content(
    req: ContentCreate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ContentResponse:
    """콘텐츠 생성."""
    crud = ContentCRUD(session)
    content = await crud.create_content(req)
    return _content_resp(content)


@router.get("", response_model=list[ContentResponse])
async def list_contents(
    status_filter: str | None = None,
    content_type: str | None = None,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ContentResponse]:
    """콘텐츠 목록."""
    crud = ContentCRUD(session)
    items = await crud.list_contents(
        status=status_filter, content_type=content_type
    )
    return [_content_resp(c) for c in items]


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ContentResponse:
    """콘텐츠 상세."""
    crud = ContentCRUD(session)
    content = await crud.get_content(content_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="콘텐츠를 찾을 수 없습니다.",
        )
    return _content_resp(content)


@router.patch("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    req: ContentUpdate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ContentResponse:
    """콘텐츠 수정."""
    crud = ContentCRUD(session)
    content = await crud.update_content(content_id, req)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="콘텐츠를 찾을 수 없습니다.",
        )
    return _content_resp(content)


@router.post("/{content_id}/advance", response_model=ContentResponse)
async def advance_pipeline(
    content_id: str,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ContentResponse:
    """파이프라인 다음 단계 진행."""
    crud = ContentCRUD(session)
    content = await crud.advance_pipeline(content_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="콘텐츠를 찾을 수 없습니다.",
        )
    return _content_resp(content)


# -- Schedule --


@router.post("/schedules", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    req: ScheduleCreate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ScheduleResponse:
    """스케줄 생성."""
    crud = ContentCRUD(session)
    schedule = await crud.create_schedule(req)
    return _schedule_resp(schedule)


@router.get("/schedules", response_model=list[ScheduleResponse])
async def list_schedules(
    active_only: bool = True,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ScheduleResponse]:
    """스케줄 목록."""
    crud = ContentCRUD(session)
    items = await crud.list_schedules(active_only=active_only)
    return [_schedule_resp(s) for s in items]


@router.patch("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    req: ScheduleUpdate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ScheduleResponse:
    """스케줄 수정."""
    crud = ContentCRUD(session)
    schedule = await crud.update_schedule(schedule_id, req)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스케줄을 찾을 수 없습니다.",
        )
    return _schedule_resp(schedule)


@router.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: str,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """스케줄 삭제."""
    crud = ContentCRUD(session)
    deleted = await crud.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스케줄을 찾을 수 없습니다.",
        )
