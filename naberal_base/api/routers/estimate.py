"""
Estimate Router - DEPRECATED SHIM for backward compatibility

This router provides a deprecated alias for POST /v1/estimate
that internally delegates to K-PEW's /v1/estimate/plan endpoint.

DEPRECATION NOTICE:
- POST /v1/estimate is DEPRECATED, use POST /v1/estimate/plan instead
- This endpoint will be removed after sunset date (90 days from deployment)
- Deprecation header and sunset date are added to all responses

Contract-First + Evidence-Gated + Zero-Mock
"""

import logging
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.routers.kpew import generate_plan, PlanRequest, PlanResponse

logger = logging.getLogger(__name__)

# DEPRECATED: This router only provides backward-compatible alias
# All actual implementation is in kpew.py
router = APIRouter(prefix="", tags=["estimate-deprecated"])

# Sunset date: 90 days from now (override with KIS_ALIAS_SUNSET env var)
SUNSET_DATE = os.getenv(
    "KIS_ALIAS_SUNSET",
    (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ"),
)


def add_deprecation_headers(response: Response) -> None:
    """Add deprecation and sunset headers to response"""
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = SUNSET_DATE
    response.headers["Link"] = (
        '</v1/estimate/plan>; rel="alternate"; title="Use this endpoint instead"'
    )
    response.headers["X-KIS-Deprecation-Reason"] = (
        "Migrating to K-PEW Plan-Execute architecture"
    )


@router.post(
    "/v1/estimate", response_model=PlanResponse, status_code=201, deprecated=True
)
async def create_estimate_deprecated(
    req: PlanRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    """
    [DEPRECATED] Generate EPDL plan (backward compatibility alias)

    ⚠️ DEPRECATION NOTICE:
    This endpoint is DEPRECATED and will be removed after {sunset_date}.

    Please migrate to: POST /v1/estimate/plan

    This endpoint is a shim that internally delegates to /v1/estimate/plan.
    The API contract is identical - only the URL path changes.

    Migration Guide:
    - Change: POST /v1/estimate → POST /v1/estimate/plan
    - Request/Response schemas: UNCHANGED
    - Authentication: UNCHANGED

    Sunset Date: {sunset_date}

    Args:
        req: Plan generation request (same as /v1/estimate/plan)
        response: FastAPI response object (for headers)
        db: Database session

    Returns:
        PlanResponse: Same as /v1/estimate/plan response

    Raises:
        HTTPException: Same errors as /v1/estimate/plan
    """
    # Add deprecation headers
    add_deprecation_headers(response)

    # Log deprecation warning
    logger.warning(
        f"[DEPRECATED] POST /v1/estimate called (use /v1/estimate/plan instead). "
        f"Sunset: {SUNSET_DATE}"
    )

    # Delegate to K-PEW's generate_plan (權威)
    # This ensures 100% identical behavior - no shim-specific logic
    try:
        return await generate_plan(req, db)
    except Exception as e:
        # Re-raise with deprecation context
        logger.error(f"[DEPRECATED SHIM] Error delegating to generate_plan: {e}")
        raise


# NOTE: GET /v1/estimate/{id} is NOT included here
# Authority for retrieval is kpew.py's GET /v1/estimate/{id}
# No duplicate/conflicting endpoints allowed (Contract-First principle)
