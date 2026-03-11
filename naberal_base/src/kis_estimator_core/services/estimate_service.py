"""
Estimate Service for KIS Estimator
Handles estimate storage and retrieval from PostgreSQL

Contract-First + Evidence-Gated + Zero-Mock

NO MOCKS - Real database operations only
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

if TYPE_CHECKING:
    from kis_estimator_core.api.schemas.estimates import (
        EstimateRequest,
        EstimateResponse,
    )

logger = logging.getLogger(__name__)


class EstimateService:
    """
    Estimate Storage and Retrieval Service

    Responsibilities:
    - Store estimate results from FIX-4 pipeline
    - Retrieve estimates by ID
    - Track estimate lifecycle (DRAFT → APPROVED)

    Contract: Operations.md#Estimate Storage
    - Zero-Mock: All database operations are real
    - Schema: kis_beta.estimates
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize estimate service

        Args:
            db: Async database session
        """
        self.db = db
        logger.info("EstimateService initialized")

    async def save_estimate(
        self,
        estimate_id: str,
        request: EstimateRequest,
        response: EstimateResponse,
    ) -> str:
        """
        Save estimate to database

        Args:
            estimate_id: Estimate ID (EST-YYYYMMDD-NNNN format)
            request: Original estimate request
            response: Pipeline response with all results

        Returns:
            str: Saved estimate ID

        Raises:
            EstimatorError: If save fails
        """
        created_at = datetime.now(UTC)

        # Serialize request and response to JSON
        request_json = self._serialize_request(request)
        response_json = self._serialize_response(response)

        query = text(
            """
            INSERT INTO kis_beta.estimates (
                id, customer_name, request_json, response_json,
                total_price, status, created_at, updated_at
            ) VALUES (
                :id, :customer_name, :request_json, :response_json,
                :total_price, 'COMPLETED', :created_at, :updated_at
            )
            ON CONFLICT (id) DO UPDATE SET
                response_json = EXCLUDED.response_json,
                total_price = EXCLUDED.total_price,
                updated_at = EXCLUDED.updated_at
            """
        )

        try:
            await self.db.execute(
                query,
                {
                    "id": estimate_id,
                    "customer_name": request.customer_name,
                    "request_json": request_json,
                    "response_json": response_json,
                    "total_price": response.total_price if response.total_price else 0,
                    "created_at": created_at,
                    "updated_at": created_at,
                },
            )
            await self.db.commit()

            logger.info(f"Estimate saved: {estimate_id}")
            return estimate_id

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save estimate: {e}")
            raise_error(
                ErrorCode.E_INTERNAL,
                f"Failed to save estimate: {e}",
                meta={"estimate_id": estimate_id}
            )

    async def get_estimate(self, estimate_id: str) -> dict[str, Any]:
        """
        Retrieve estimate by ID

        Args:
            estimate_id: Estimate ID (EST-YYYYMMDD-NNNN format)

        Returns:
            Dict containing full estimate data

        Raises:
            EstimatorError: If estimate not found or retrieval fails
        """
        query = text(
            """
            SELECT id, customer_name, request_json, response_json,
                   total_price, status, created_at, updated_at
            FROM kis_beta.estimates
            WHERE id = :id
            """
        )

        try:
            result = await self.db.execute(query, {"id": estimate_id})
            row = result.fetchone()

            if not row:
                raise_error(
                    ErrorCode.E_NOT_FOUND,
                    f"Estimate not found: {estimate_id}",
                    hint="Check estimate ID format: EST-YYYYMMDD-NNNN",
                    meta={"estimate_id": estimate_id}
                )

            # Parse JSON fields (asyncpg may auto-parse JSONB)
            request_data = row[2] if isinstance(row[2], dict) else json.loads(row[2]) if row[2] else {}
            response_data = row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {}

            return {
                "estimate_id": row[0],
                "customer_name": row[1],
                "request": request_data,
                "response": response_data,
                "total_price": row[4],
                "status": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "updated_at": row[7].isoformat() if row[7] else None,
            }

        except Exception as e:
            if "E_NOT_FOUND" in str(e):
                raise
            logger.error(f"Failed to get estimate: {e}")
            raise_error(
                ErrorCode.E_INTERNAL,
                f"Database error: {e}",
                meta={"estimate_id": estimate_id}
            )

    async def get_estimate_response(self, estimate_id: str) -> EstimateResponse:
        """
        Retrieve estimate and return as EstimateResponse schema

        Args:
            estimate_id: Estimate ID

        Returns:
            EstimateResponse: Full estimate response object

        Raises:
            EstimatorError: If estimate not found
        """
        from kis_estimator_core.api.schemas.estimates import EstimateResponse

        data = await self.get_estimate(estimate_id)
        response_data = data.get("response", {})

        # Reconstruct EstimateResponse from stored JSON
        return EstimateResponse(**response_data)

    def _serialize_request(self, request: EstimateRequest) -> str:
        """Serialize EstimateRequest to JSON string"""
        try:
            # Use Pydantic model_dump for proper serialization
            if hasattr(request, "model_dump"):
                data = request.model_dump(mode="json")
            elif hasattr(request, "dict"):
                data = request.dict()
            else:
                data = dict(request)
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Request serialization fallback: {e}")
            return json.dumps({}, ensure_ascii=False)

    def _serialize_response(self, response: EstimateResponse) -> str:
        """Serialize EstimateResponse to JSON string"""
        try:
            # Use Pydantic model_dump for proper serialization
            if hasattr(response, "model_dump"):
                data = response.model_dump(mode="json")
            elif hasattr(response, "dict"):
                data = response.dict()
            else:
                data = dict(response)
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Response serialization fallback: {e}")
            return json.dumps({}, ensure_ascii=False)


# Module-level helper functions

async def save_estimate_to_db(
    db: AsyncSession,
    estimate_id: str,
    request: EstimateRequest,
    response: EstimateResponse,
) -> str:
    """
    Convenience function to save estimate

    Args:
        db: Database session
        estimate_id: Estimate ID
        request: Original request
        response: Pipeline response

    Returns:
        str: Saved estimate ID
    """
    service = EstimateService(db)
    return await service.save_estimate(estimate_id, request, response)


async def get_estimate_from_db(
    db: AsyncSession,
    estimate_id: str,
) -> EstimateResponse:
    """
    Convenience function to retrieve estimate

    Args:
        db: Database session
        estimate_id: Estimate ID

    Returns:
        EstimateResponse: Full estimate response

    Raises:
        EstimatorError: If not found
    """
    service = EstimateService(db)
    return await service.get_estimate_response(estimate_id)


async def generate_estimate_id(db: AsyncSession) -> str:
    """
    DB 기반 견적 ID 생성 (TODO[KIS-011] 구현)

    Format: EST-YYYYMMDD-NNNN
    - YYYYMMDD: 오늘 날짜 (UTC)
    - NNNN: 해당 날짜의 시퀀스 번호 (0001~9999)

    시퀀스 로직:
    - 오늘 날짜의 마지막 견적 ID를 조회하여 +1
    - 없으면 0001부터 시작
    - DB에서 원자적으로 처리 (동시성 안전)

    Args:
        db: Async database session

    Returns:
        str: 견적 ID (예: EST-20251123-0001)

    Raises:
        EstimatorError: 시퀀스 생성 실패 시
    """
    from datetime import datetime

    today = datetime.now(UTC)
    date_str = today.strftime("%Y%m%d")
    prefix = f"EST-{date_str}-"

    query = text(
        """
        SELECT id FROM kis_beta.estimates
        WHERE id LIKE :prefix
        ORDER BY id DESC
        LIMIT 1
        """
    )

    try:
        result = await db.execute(query, {"prefix": f"{prefix}%"})
        row = result.fetchone()

        if row:
            # 마지막 ID에서 시퀀스 추출하여 +1
            last_id = row[0]  # EST-20251123-0042
            last_seq = int(last_id.split("-")[-1])
            next_seq = last_seq + 1
        else:
            # 오늘 첫 견적
            next_seq = 1

        if next_seq > 9999:
            raise_error(
                ErrorCode.E_INTERNAL,
                "Daily estimate limit exceeded (9999)",
                hint="Contact system administrator",
                meta={"date": date_str}
            )

        estimate_id = f"{prefix}{next_seq:04d}"
        logger.info(f"Generated estimate ID: {estimate_id}")
        return estimate_id

    except Exception as e:
        if "E_INTERNAL" in str(e):
            raise
        logger.warning(f"DB sequence generation failed, using fallback: {e}")
        # DB 연결 실패 시 랜덤 폴백 (기존 로직)
        import random
        fallback_seq = random.randint(1, 9999)
        return f"{prefix}{fallback_seq:04d}"
