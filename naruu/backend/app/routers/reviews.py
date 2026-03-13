"""Review management: CRUD, AI sentiment analysis, AI response generation."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.review import Review, ReviewPlatform
from app.models.user import User
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/reviews", tags=["reviews"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ReviewCreate(BaseModel):
    customer_id: int | None = None
    partner_id: int | None = None
    platform: ReviewPlatform
    rating: float | None = None
    content_ja: str | None = None
    content_ko: str | None = None


class ReviewUpdate(BaseModel):
    rating: float | None = None
    content_ja: str | None = None
    content_ko: str | None = None
    is_published: bool | None = None
    response_text: str | None = None


class ReviewOut(BaseModel):
    id: int
    customer_id: int | None = None
    partner_id: int | None = None
    platform: ReviewPlatform
    rating: float | None = None
    content_ja: str | None = None
    content_ko: str | None = None
    sentiment_score: float | None = None
    is_published: bool
    response_text: str | None = None
    responded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    items: list[ReviewOut]
    total: int
    page: int
    per_page: int


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    platform: ReviewPlatform | None = None,
    has_response: bool | None = None,
    min_sentiment: float | None = None,
    max_sentiment: float | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = select(Review)

    if platform:
        q = q.where(Review.platform == platform)
    if has_response is True:
        q = q.where(Review.response_text.isnot(None))
    elif has_response is False:
        q = q.where(Review.response_text.is_(None))
    if min_sentiment is not None:
        q = q.where(Review.sentiment_score >= min_sentiment)
    if max_sentiment is not None:
        q = q.where(Review.sentiment_score <= max_sentiment)
    if search:
        pattern = f"%{search}%"
        q = q.where(
            (Review.content_ja.ilike(pattern)) | (Review.content_ko.ilike(pattern))
        )

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Review.created_at.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    return ReviewListResponse(
        items=[ReviewOut.model_validate(r) for r in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/stats")
async def review_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Review analytics overview."""
    from sqlalchemy import case

    # Consolidated aggregation: total, avg_rating, avg_sentiment, no_response,
    # and sentiment distribution in a single query
    agg_q = select(
        func.count(Review.id),
        func.avg(Review.rating),
        func.avg(Review.sentiment_score),
        func.count(case((Review.response_text.is_(None), 1))),
        func.count(case((Review.sentiment_score >= 0.7, 1))),
        func.count(case((and_(Review.sentiment_score >= 0.4, Review.sentiment_score < 0.7), 1))),
        func.count(case((Review.sentiment_score < 0.4, 1))),
    )
    agg_result = (await db.execute(agg_q)).one()
    total, avg_rating, avg_sentiment, no_response, positive, neutral, negative = agg_result

    # By platform (single GROUP BY query)
    platform_q = (
        select(Review.platform, func.count(Review.id), func.avg(Review.sentiment_score))
        .group_by(Review.platform)
    )
    platform_result = await db.execute(platform_q)
    by_platform = [
        {
            "platform": row[0].value,
            "count": row[1],
            "avg_sentiment": round(row[2], 3) if row[2] else None,
        }
        for row in platform_result.all()
    ]

    return {
        "total": total,
        "avg_rating": round(avg_rating, 2) if avg_rating else None,
        "avg_sentiment": round(avg_sentiment, 3) if avg_sentiment else None,
        "awaiting_response": no_response,
        "by_platform": by_platform,
        "sentiment_distribution": {
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
        },
    }


@router.get("/{review_id}", response_model=ReviewOut)
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, "Review not found")
    return ReviewOut.model_validate(review)


@router.post("", response_model=ReviewOut, status_code=201)
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    review = Review(**data.model_dump())
    db.add(review)
    await db.flush()
    await db.refresh(review)
    return ReviewOut.model_validate(review)


@router.put("/{review_id}", response_model=ReviewOut)
async def update_review(
    review_id: int,
    data: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, "Review not found")

    update_data = data.model_dump(exclude_unset=True)
    if "response_text" in update_data and update_data["response_text"]:
        update_data["responded_at"] = datetime.now(timezone.utc)

    for key, value in update_data.items():
        setattr(review, key, value)

    await db.flush()
    await db.refresh(review)
    return ReviewOut.model_validate(review)


# ---------------------------------------------------------------------------
# AI Features
# ---------------------------------------------------------------------------


@router.post("/{review_id}/analyze", response_model=ReviewOut)
async def analyze_sentiment(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """AI sentiment analysis for a review."""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, "Review not found")

    content = review.content_ja or review.content_ko
    if not content:
        raise HTTPException(400, "No review content to analyze")

    system = (
        "あなたは感情分析の専門家です。"
        "レビューテキストの感情スコアを0.0（非常にネガティブ）〜1.0（非常にポジティブ）で評価してください。"
        "数値のみ回答してください。例: 0.85"
    )

    ai = get_ai_service()
    reply = await ai.chat(content, system_prompt=system, max_tokens=10)

    if reply:
        try:
            score = float(reply.strip())
            score = max(0.0, min(1.0, score))
            review.sentiment_score = score
            await db.flush()
            await db.refresh(review)
        except ValueError:
            pass

    return ReviewOut.model_validate(review)


@router.post("/{review_id}/generate-response")
async def generate_response(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """AI-generated response suggestion for a review."""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, "Review not found")

    content = review.content_ja or review.content_ko
    if not content:
        raise HTTPException(400, "No review content")

    sentiment_hint = ""
    if review.sentiment_score is not None:
        if review.sentiment_score >= 0.7:
            sentiment_hint = "このレビューはポジティブです。感謝を伝えてください。"
        elif review.sentiment_score >= 0.4:
            sentiment_hint = "このレビューは中立的です。丁寧に対応してください。"
        else:
            sentiment_hint = "このレビューはネガティブです。誠意をもって改善を約束してください。"

    system = (
        "あなたはNARUU（ナル）のカスタマーサポート担当です。"
        "顧客のレビューに対する返信を日本語で作成してください。"
        "丁寧で誠実な口調を使い、具体的な内容に言及してください。"
        "医療効果の保証は絶対にしないでください。"
        f"\n{sentiment_hint}"
    )

    ai = get_ai_service()
    reply = await ai.chat(
        f"以下のレビューへの返信を作成:\n\n{content}",
        system_prompt=system,
        max_tokens=500,
    )

    return {"response": reply or "AI応答を生成できませんでした。"}
