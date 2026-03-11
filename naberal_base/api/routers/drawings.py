"""
Drawing Router - Endpoints for generating manufacturing drawings
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from kis_estimator_core.services.drawing_service import DrawingService
from kis_estimator_core.core.ssot.errors import EstimatorError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/drawings", tags=["drawings"])

@router.post("/from-estimate/{estimate_id}")
async def create_drawing(estimate_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generate manufacturing drawings (SVG/DXF) for a given estimate.
    
    Flow:
    1. Check if estimate exists and has completed Layout stage
    2. Call DrawingService to generate drawing
    3. Return drawing metadata and path
    """
    try:
        service = DrawingService(db)
        result = await service.generate_drawing(estimate_id)
        return result
        
    except EstimatorError as e:
        raise HTTPException(
            status_code=400, # or 404 depending on error
            detail={
                "code": e.error_code.code,
                "message": e.error_code.message,
                "hint": e.error_code.hint
            }
        )
    except Exception as e:
        logger.exception(f"Failed to generate drawing for {estimate_id}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        )
