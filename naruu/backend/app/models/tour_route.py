"""Tour route model for Google Maps-based tourist route planning."""

import enum
from typing import Optional

from sqlalchemy import ARRAY, Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class RouteStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class TourRoute(Base, TimestampMixin):
    """A planned tourist route with waypoints stored as JSONB.

    waypoints format:
    [
        {
            "order": 1,
            "place_id": "ChIJ...",
            "name_ja": "大邱東城路",
            "name_ko": "대구 동성로",
            "lat": 35.8714,
            "lng": 128.5964,
            "category": "tourism|medical|restaurant|hotel|shopping",
            "stay_minutes": 60,
            "notes": "optional notes",
            "partner_id": null  // link to partners table if applicable
        }
    ]

    route_data format (cached from Google Directions API):
    {
        "total_distance_km": 12.5,
        "total_duration_minutes": 180,
        "legs": [
            {
                "from": "동성로",
                "to": "수성못",
                "distance_km": 3.2,
                "duration_minutes": 15,
                "polyline": "encoded_polyline_string"
            }
        ]
    }
    """
    __tablename__ = "tour_routes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_ja: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    description_ja: Mapped[str | None] = mapped_column(Text)
    description_ko: Mapped[str | None] = mapped_column(Text)

    # Route data
    waypoints: Mapped[dict | None] = mapped_column(JSONB, default=list)
    route_data: Mapped[dict | None] = mapped_column(JSONB)

    # Metadata
    status: Mapped[RouteStatus] = mapped_column(
        Enum(RouteStatus, name="route_status"),
        default=RouteStatus.DRAFT,
        nullable=False,
    )
    total_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    total_distance_km: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)))
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relations
    customer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("customers.id"), index=True
    )
    package_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("packages.id")
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id")
    )
