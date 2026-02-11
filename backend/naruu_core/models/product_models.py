"""Tour Product (Package/Course) Pydantic models"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ItineraryItem(BaseModel):
    day: int = 1
    time: str
    venue_id: Optional[str] = None
    activity_ja: str
    activity_kr: Optional[str] = None
    duration_min: Optional[int] = None


class ProductCreate(BaseModel):
    name_ja: str = Field(..., min_length=1, max_length=200)
    name_kr: Optional[str] = Field(None, max_length=200)
    product_type: str = Field(..., pattern="^(package|course|single_service)$")
    category: Optional[str] = Field(None, pattern="^(medical|beauty|tourism|mixed)$")
    base_price_jpy: Optional[float] = Field(None, ge=0)
    base_price_krw: Optional[float] = Field(None, ge=0)
    description_ja: Optional[str] = None
    description_kr: Optional[str] = None
    highlights_ja: list[str] = []
    includes: list[str] = []
    excludes: list[str] = []
    duration_days: int = Field(default=1, ge=1)
    min_participants: int = Field(default=1, ge=1)
    max_participants: int = Field(default=10, ge=1)
    itinerary: list[ItineraryItem] = []
    venue_ids: list[str] = []
    thumbnail_url: Optional[str] = None
    photos: list[str] = []
    status: str = "draft"
    is_featured: bool = False


class ProductUpdate(BaseModel):
    name_ja: Optional[str] = None
    name_kr: Optional[str] = None
    product_type: Optional[str] = None
    category: Optional[str] = None
    base_price_jpy: Optional[float] = None
    base_price_krw: Optional[float] = None
    description_ja: Optional[str] = None
    description_kr: Optional[str] = None
    highlights_ja: Optional[list[str]] = None
    includes: Optional[list[str]] = None
    excludes: Optional[list[str]] = None
    duration_days: Optional[int] = None
    itinerary: Optional[list[ItineraryItem]] = None
    venue_ids: Optional[list[str]] = None
    photos: Optional[list[str]] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None


class ProductResponse(BaseModel):
    id: str
    code: Optional[str] = None
    name_ja: str
    name_kr: Optional[str] = None
    product_type: str
    category: Optional[str] = None
    base_price_jpy: Optional[float] = None
    base_price_krw: Optional[float] = None
    description_ja: Optional[str] = None
    highlights_ja: list[str] = []
    includes: list[str] = []
    excludes: list[str] = []
    duration_days: int = 1
    min_participants: int = 1
    max_participants: int = 10
    itinerary: list[dict] = []
    venue_ids: list[str] = []
    thumbnail_url: Optional[str] = None
    photos: list[str] = []
    status: str = "draft"
    is_featured: bool = False
    created_at: Optional[datetime] = None


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
