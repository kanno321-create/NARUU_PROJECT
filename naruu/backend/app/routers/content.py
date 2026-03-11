"""Content management: CRUD, approval workflow, Make.com webhook trigger."""

from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.content import Content, ContentPlatform, ContentSeries, ContentStatus
from app.models.user import User
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/content", tags=["content"])
settings = get_settings()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ContentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    series: ContentSeries
    script_ja: str | None = None
    script_ko: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    platform: ContentPlatform | None = None


class ContentUpdate(BaseModel):
    title: str | None = None
    series: ContentSeries | None = None
    script_ja: str | None = None
    script_ko: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    platform: ContentPlatform | None = None


class ContentOut(BaseModel):
    id: int
    title: str
    series: ContentSeries
    script_ja: str | None = None
    script_ko: str | None = None
    status: ContentStatus
    video_url: str | None = None
    thumbnail_url: str | None = None
    platform: ContentPlatform | None = None
    published_at: datetime | None = None
    performance_metrics: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentListResponse(BaseModel):
    items: list[ContentOut]
    total: int
    page: int
    per_page: int


class ApprovalAction(BaseModel):
    action: str  # "approve" | "reject" | "request_review"
    comment: str | None = None


class MakeWebhookTrigger(BaseModel):
    content_id: int
    blueprint: str  # "story_video" | "brochure"
    params: dict | None = None


class ScriptGenerateRequest(BaseModel):
    series: ContentSeries
    topic: str
    tone: str = "friendly"  # friendly|professional|casual
    length: str = "medium"  # short|medium|long


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=ContentListResponse)
async def list_content(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    series: ContentSeries | None = None,
    status: ContentStatus | None = None,
    platform: ContentPlatform | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = select(Content)

    if series:
        q = q.where(Content.series == series)
    if status:
        q = q.where(Content.status == status)
    if platform:
        q = q.where(Content.platform == platform)
    if search:
        q = q.where(Content.title.ilike(f"%{search}%"))

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Content.created_at.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    return ContentListResponse(
        items=[ContentOut.model_validate(c) for c in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{content_id}", response_model=ContentOut)
async def get_content(
    content_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(404, "Content not found")
    return ContentOut.model_validate(content)


@router.post("", response_model=ContentOut, status_code=201)
async def create_content(
    data: ContentCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    content = Content(**data.model_dump(), status=ContentStatus.DRAFT)
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return ContentOut.model_validate(content)


@router.put("/{content_id}", response_model=ContentOut)
async def update_content(
    content_id: int,
    data: ContentUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(404, "Content not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(content, key, value)

    await db.commit()
    await db.refresh(content)
    return ContentOut.model_validate(content)


@router.delete("/{content_id}")
async def delete_content(
    content_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(404, "Content not found")

    await db.delete(content)
    await db.commit()
    return {"message": "Content deleted"}


# ---------------------------------------------------------------------------
# Approval Workflow
# ---------------------------------------------------------------------------


VALID_TRANSITIONS = {
    ContentStatus.DRAFT: [ContentStatus.REVIEW],
    ContentStatus.REVIEW: [ContentStatus.APPROVED, ContentStatus.REJECTED],
    ContentStatus.APPROVED: [ContentStatus.PUBLISHED],
    ContentStatus.REJECTED: [ContentStatus.DRAFT],
    ContentStatus.PUBLISHED: [],
}


@router.post("/{content_id}/workflow", response_model=ContentOut)
async def workflow_action(
    content_id: int,
    action: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Progress content through the approval workflow.

    Flow: draft → review → approved → published
                         ↘ rejected → draft (restart)
    """
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(404, "Content not found")

    action_map = {
        "request_review": ContentStatus.REVIEW,
        "approve": ContentStatus.APPROVED,
        "reject": ContentStatus.REJECTED,
        "publish": ContentStatus.PUBLISHED,
        "revert_draft": ContentStatus.DRAFT,
    }

    target_status = action_map.get(action.action)
    if not target_status:
        raise HTTPException(400, f"Unknown action: {action.action}")

    valid_targets = VALID_TRANSITIONS.get(content.status, [])
    if target_status not in valid_targets:
        raise HTTPException(
            400,
            f"Cannot transition from {content.status.value} to {target_status.value}. "
            f"Valid: {[s.value for s in valid_targets]}",
        )

    content.status = target_status
    if target_status == ContentStatus.PUBLISHED:
        content.published_at = datetime.utcnow()

    await db.commit()
    await db.refresh(content)
    return ContentOut.model_validate(content)


# ---------------------------------------------------------------------------
# Make.com Webhook Integration
# ---------------------------------------------------------------------------


@router.post("/trigger-make")
async def trigger_make_webhook(
    data: MakeWebhookTrigger,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Trigger Make.com blueprint for video/brochure generation."""
    result = await db.execute(select(Content).where(Content.id == data.content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(404, "Content not found")

    webhook_url = None
    if data.blueprint == "story_video":
        webhook_url = settings.MAKE_STORY_WEBHOOK_URL
    elif data.blueprint == "brochure":
        webhook_url = settings.MAKE_BROCHURE_WEBHOOK_URL

    if not webhook_url:
        raise HTTPException(503, f"Make.com webhook not configured for '{data.blueprint}'")

    payload = {
        "content_id": content.id,
        "title": content.title,
        "series": content.series.value,
        "script_ja": content.script_ja,
        "script_ko": content.script_ko,
        **(data.params or {}),
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(webhook_url, json=payload)

    if resp.status_code not in (200, 201, 202):
        raise HTTPException(502, f"Make.com webhook failed: {resp.status_code}")

    return {
        "message": f"Make.com blueprint '{data.blueprint}' triggered",
        "content_id": content.id,
        "webhook_status": resp.status_code,
    }


# ---------------------------------------------------------------------------
# AI Script Generation
# ---------------------------------------------------------------------------


@router.post("/generate-script")
async def generate_script(
    req: ScriptGenerateRequest,
    _user: User = Depends(get_current_user),
):
    """AI-powered script generation for video/brochure content."""
    series_descriptions = {
        ContentSeries.DAEGU_TOUR: "大邱の観光スポットを紹介する動画シリーズ",
        ContentSeries.JCOUPLE: "日韓カップルの大邱生活・観光体験シリーズ",
        ContentSeries.MEDICAL: "大邱の医療観光・美容施術を紹介するシリーズ",
        ContentSeries.BROCHURE: "大邱観光のパンフレット・ガイドブック",
    }

    length_tokens = {"short": 500, "medium": 1000, "long": 1500}

    tone_instructions = {
        "friendly": "親しみやすくカジュアルな口調で、絵文字も適度に使用",
        "professional": "プロフェッショナルで信頼感のある丁寧な口調",
        "casual": "とてもカジュアルで若者向けの口調、SNS風",
    }

    system_prompt = (
        "あなたはNARUU（ナル）のコンテンツクリエイターAIです。"
        "大邱の美容観光・医療観光コンテンツを制作する専門家です。"
        f"シリーズ: {series_descriptions.get(req.series, req.series.value)}\n"
        f"トーン: {tone_instructions.get(req.tone, req.tone)}\n"
        "医療効果の保証や誇大広告は絶対にしないでください。\n"
        "日本語と韓国語の両方でスクリプトを作成してください。\n"
        "フォーマット:\n"
        "【日本語スクリプト】\n(日本語の内容)\n\n"
        "【韓国語スクリプト】\n(韓国語の内容)"
    )

    user_message = f"テーマ: {req.topic}\nこのテーマで動画/コンテンツのスクリプトを作成してください。"

    ai = get_ai_service()
    reply = await ai.chat(
        user_message,
        system_prompt=system_prompt,
        max_tokens=length_tokens.get(req.length, 1000),
    )

    if not reply:
        raise HTTPException(502, "AI service unavailable")

    # Parse bilingual script
    script_ja = ""
    script_ko = ""
    if "【日本語スクリプト】" in reply and "【韓国語スクリプト】" in reply:
        parts = reply.split("【韓国語スクリプト】")
        script_ja = parts[0].replace("【日本語スクリプト】", "").strip()
        script_ko = parts[1].strip() if len(parts) > 1 else ""
    else:
        script_ja = reply

    return {
        "script_ja": script_ja,
        "script_ko": script_ko,
        "raw": reply,
    }


# ---------------------------------------------------------------------------
# Content Stats
# ---------------------------------------------------------------------------


@router.get("/stats/overview")
async def content_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Get content pipeline overview stats."""
    counts = {}
    for status in ContentStatus:
        q = select(func.count(Content.id)).where(Content.status == status)
        counts[status.value] = (await db.execute(q)).scalar() or 0

    series_counts = {}
    for series in ContentSeries:
        q = select(func.count(Content.id)).where(Content.series == series)
        series_counts[series.value] = (await db.execute(q)).scalar() or 0

    return {
        "by_status": counts,
        "by_series": series_counts,
        "total": sum(counts.values()),
    }
