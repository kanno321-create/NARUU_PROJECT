"""Customer (Japanese Tourist) Pydantic models"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name_ja: str = Field(..., min_length=1, max_length=100, description="Japanese name")
    name_kr: Optional[str] = Field(None, max_length=100)
    name_en: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    birth_date: Optional[date] = None
    nationality: str = "JP"
    email: Optional[str] = None
    phone: Optional[str] = None
    line_user_id: Optional[str] = None
    instagram_handle: Optional[str] = None
    language_preference: str = "ja"
    medical_interests: list[str] = []
    beauty_interests: list[str] = []
    tourism_interests: list[str] = []
    dietary_restrictions: list[str] = []
    allergies: Optional[str] = None
    customer_source: Optional[str] = Field(None, pattern="^(line|instagram|website|referral|walk_in|other)$")
    vip_level: str = "normal"
    memo: Optional[str] = None


class CustomerUpdate(BaseModel):
    name_ja: Optional[str] = Field(None, min_length=1, max_length=100)
    name_kr: Optional[str] = None
    name_en: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    line_user_id: Optional[str] = None
    instagram_handle: Optional[str] = None
    language_preference: Optional[str] = None
    medical_interests: Optional[list[str]] = None
    beauty_interests: Optional[list[str]] = None
    tourism_interests: Optional[list[str]] = None
    customer_source: Optional[str] = None
    vip_level: Optional[str] = None
    memo: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    id: str
    code: Optional[str] = None
    name_ja: str
    name_kr: Optional[str] = None
    name_en: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    nationality: str = "JP"
    email: Optional[str] = None
    phone: Optional[str] = None
    line_user_id: Optional[str] = None
    instagram_handle: Optional[str] = None
    language_preference: str = "ja"
    medical_interests: list[str] = []
    beauty_interests: list[str] = []
    tourism_interests: list[str] = []
    customer_source: Optional[str] = None
    vip_level: str = "normal"
    total_spent_jpy: float = 0
    visit_count: int = 0
    memo: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int
