"""CRM Pydantic 스키마."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# -- Customer --


class CustomerCreate(BaseModel):
    """고객 생성 요청."""

    line_user_id: str | None = None
    display_name: str = Field(min_length=1, max_length=200)
    language: str = Field(default="ja", pattern=r"^(ja|ko|en)$")
    phone: str = ""
    email: str = ""
    notes: str = ""


class CustomerUpdate(BaseModel):
    """고객 수정 요청."""

    display_name: str | None = None
    language: str | None = Field(default=None, pattern=r"^(ja|ko|en)$")
    phone: str | None = None
    email: str | None = None
    status: str | None = Field(
        default=None, pattern=r"^(active|inactive|blocked)$"
    )
    notes: str | None = None


class CustomerResponse(BaseModel):
    """고객 응답."""

    id: str
    line_user_id: str | None
    display_name: str
    language: str
    phone: str
    email: str
    status: str
    notes: str


# -- Booking --

BOOKING_STATUSES = ("inquiry", "confirmed", "completed", "cancelled")


class BookingCreate(BaseModel):
    """예약 생성 요청."""

    customer_id: str
    partner_id: str = ""
    service_name: str = ""
    price_krw: int = Field(default=0, ge=0)
    commission_krw: int = Field(default=0, ge=0)
    scheduled_at: datetime | None = None
    notes: str = ""


class BookingUpdate(BaseModel):
    """예약 수정 요청."""

    status: str | None = Field(
        default=None,
        pattern=r"^(inquiry|confirmed|completed|cancelled)$",
    )
    partner_id: str | None = None
    service_name: str | None = None
    price_krw: int | None = Field(default=None, ge=0)
    commission_krw: int | None = Field(default=None, ge=0)
    scheduled_at: datetime | None = None
    notes: str | None = None


class BookingResponse(BaseModel):
    """예약 응답."""

    id: str
    customer_id: str
    partner_id: str
    service_name: str
    status: str
    price_krw: int
    commission_krw: int
    scheduled_at: datetime | None
    notes: str


# -- Interaction --


class InteractionCreate(BaseModel):
    """상호작용 기록 요청."""

    customer_id: str
    channel: str = Field(pattern=r"^(line|web|phone)$")
    direction: str = Field(pattern=r"^(inbound|outbound)$")
    content: str = ""
    metadata_json: str = "{}"


class InteractionResponse(BaseModel):
    """상호작용 응답."""

    id: str
    customer_id: str
    channel: str
    direction: str
    content: str
    metadata_json: str
