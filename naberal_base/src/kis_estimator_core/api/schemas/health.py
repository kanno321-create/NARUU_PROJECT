"""
Health Check Response Schemas

OpenAPI 3.1 스키마 기반 Pydantic 모델
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Health check 응답

    Contract: spec_kit/api/openapi.yaml#HealthResponse
    """

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ...,
        description="전체 시스템 상태"
    )

    timestamp: datetime = Field(
        ...,
        description="확인 일시 (ISO 8601)"
    )

    checks: dict[str, Literal["ok", "degraded", "error"]] = Field(
        ...,
        description="개별 체크 결과",
        examples=[{
            "database": "ok",
            "redis": "ok",
            "jwks": "ok",
            "catalog_cache": "ok"
        }]
    )

    uptime_seconds: int | None = Field(
        None,
        description="가동 시간 (초)",
        ge=0
    )

    errors: list[str] | None = Field(
        None,
        description="오류 메시지 목록"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-11-18T10:30:00+09:00",
                "checks": {
                    "database": "ok",
                    "knowledge_files": "ok"
                },
                "uptime_seconds": 86400
            }
        }
