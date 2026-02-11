"""Booking Pydantic models"""

from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, Field


class BookingItemCreate(BaseModel):
    partner_id: Optional[str] = None
    service_name_ja: str
    service_name_kr: Optional[str] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    price_jpy: Optional[float] = None
    price_krw: Optional[float] = None
    notes: Optional[str] = None


class BookingCreate(BaseModel):
    customer_id: str
    product_id: Optional[str] = None
    booking_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    total_price_jpy: Optional[float] = Field(None, ge=0)
    total_price_krw: Optional[float] = Field(None, ge=0)
    exchange_rate: Optional[float] = None
    payment_method: Optional[str] = Field(None, pattern="^(credit_card|bank_transfer|cash|line_pay)$")
    participants: int = Field(default=1, ge=1)
    special_requests: Optional[str] = None
    internal_notes: Optional[str] = None
    items: list[BookingItemCreate] = []


class BookingUpdate(BaseModel):
    booking_date: Optional[date] = None
    start_time: Optional[time] = None
    total_price_jpy: Optional[float] = None
    total_price_krw: Optional[float] = None
    payment_status: Optional[str] = Field(None, pattern="^(pending|partial|paid|refunded)$")
    payment_method: Optional[str] = None
    status: Optional[str] = Field(
        None, pattern="^(inquiry|confirmed|in_progress|completed|cancelled|no_show)$"
    )
    participants: Optional[int] = None
    special_requests: Optional[str] = None
    internal_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None


class BookingItemResponse(BaseModel):
    id: str
    seq: int
    partner_id: Optional[str] = None
    service_name_ja: str
    service_name_kr: Optional[str] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    price_jpy: Optional[float] = None
    price_krw: Optional[float] = None
    commission_krw: Optional[float] = None
    status: str = "pending"


class BookingResponse(BaseModel):
    id: str
    booking_no: str
    customer_id: str
    product_id: Optional[str] = None
    booking_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    total_price_jpy: Optional[float] = None
    total_price_krw: Optional[float] = None
    exchange_rate: Optional[float] = None
    commission_amount_krw: Optional[float] = None
    payment_status: str = "pending"
    payment_method: Optional[str] = None
    status: str = "inquiry"
    participants: int = 1
    special_requests: Optional[str] = None
    internal_notes: Optional[str] = None
    items: list[BookingItemResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    page_size: int
