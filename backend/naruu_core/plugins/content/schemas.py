"""콘텐츠 Pydantic 스키마."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

CONTENT_TYPES = ("video", "blog", "sns")
CONTENT_STATUSES = ("draft", "scripted", "produced", "published", "archived")
PIPELINE_STAGES = (
    "pending", "script", "image", "voice", "video", "publish", "done", "failed"
)


class ContentCreate(BaseModel):
    """콘텐츠 생성 요청."""

    title: str = Field(min_length=1, max_length=300)
    content_type: str = Field(
        default="video", pattern=r"^(video|blog|sns)$"
    )
    language: str = Field(default="ja", pattern=r"^(ja|ko|en)$")
    topic: str = ""
    script: str = ""


class ContentUpdate(BaseModel):
    """콘텐츠 수정 요청."""

    title: str | None = None
    status: str | None = Field(
        default=None,
        pattern=r"^(draft|scripted|produced|published|archived)$",
    )
    pipeline_stage: str | None = Field(
        default=None,
        pattern=r"^(pending|script|image|voice|video|publish|done|failed)$",
    )
    script: str | None = None
    cost_usd: float | None = Field(default=None, ge=0.0)
    publish_url: str | None = None
    error_message: str | None = None
    metadata_json: str | None = None


class ContentResponse(BaseModel):
    """콘텐츠 응답."""

    id: str
    title: str
    content_type: str
    language: str
    topic: str
    script: str
    status: str
    pipeline_stage: str
    cost_usd: float
    publish_url: str
    error_message: str


class ScheduleCreate(BaseModel):
    """스케줄 생성 요청."""

    name: str = Field(min_length=1, max_length=200)
    content_type: str = Field(
        default="video", pattern=r"^(video|blog|sns)$"
    )
    topic_template: str = ""
    language: str = Field(default="ja", pattern=r"^(ja|ko|en)$")
    cron_expression: str = "0 9 * * 1"


class ScheduleUpdate(BaseModel):
    """스케줄 수정 요청."""

    name: str | None = None
    topic_template: str | None = None
    cron_expression: str | None = None
    is_active: bool | None = None


class ScheduleResponse(BaseModel):
    """스케줄 응답."""

    id: str
    name: str
    content_type: str
    topic_template: str
    language: str
    cron_expression: str
    is_active: bool
    last_run_at: datetime | None
