"""관광 추천 Pydantic 스키마."""

from __future__ import annotations

from pydantic import BaseModel, Field

SPOT_CATEGORIES = ("medical", "beauty", "tourism", "food", "shopping")


class SpotCreate(BaseModel):
    """스팟 생성 요청."""

    name_ja: str = Field(min_length=1, max_length=200)
    name_ko: str = ""
    category: str = Field(
        default="tourism",
        pattern=r"^(medical|beauty|tourism|food|shopping)$",
    )
    description_ja: str = ""
    address: str = ""
    latitude: float = Field(default=0.0, ge=-90.0, le=90.0)
    longitude: float = Field(default=0.0, ge=-180.0, le=180.0)
    avg_price_krw: int = Field(default=0, ge=0)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    tags: str = ""
    partner_id: str | None = None


class SpotUpdate(BaseModel):
    """스팟 수정 요청."""

    name_ja: str | None = None
    name_ko: str | None = None
    description_ja: str | None = None
    address: str | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    avg_price_krw: int | None = Field(default=None, ge=0)
    rating: float | None = Field(default=None, ge=0.0, le=5.0)
    popularity_score: float | None = Field(default=None, ge=0.0)
    tags: str | None = None
    is_active: bool | None = None


class SpotResponse(BaseModel):
    """스팟 응답."""

    id: str
    name_ja: str
    name_ko: str
    category: str
    description_ja: str
    address: str
    latitude: float
    longitude: float
    avg_price_krw: int
    rating: float
    popularity_score: float
    tags: str
    is_active: bool
    partner_id: str | None


class RecommendRequest(BaseModel):
    """추천 요청."""

    categories: list[str] = Field(default_factory=list)
    budget_krw: int = Field(default=0, ge=0)
    latitude: float = Field(default=0.0, ge=-90.0, le=90.0)
    longitude: float = Field(default=0.0, ge=-180.0, le=180.0)
    tags: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=50)


class RecommendedSpot(BaseModel):
    """추천 결과 항목."""

    spot: SpotResponse
    score: float
    reasons: list[str]
