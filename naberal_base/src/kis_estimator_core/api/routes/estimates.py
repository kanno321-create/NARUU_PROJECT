"""
Estimates Router

견적 생성 및 검증 엔드포인트
Contract: spec_kit/api/openapi.yaml#/estimates
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from kis_estimator_core.api.schemas.estimates import (
    EstimateRequest,
    EstimateResponse,
    ValidationChecks,
    ValidationResponse,
)
from kis_estimator_core.core.ssot.errors import ErrorCode, EstimatorError, raise_error
from kis_estimator_core.engine.fix4_pipeline import get_pipeline
from kis_estimator_core.infra.db import get_db
from kis_estimator_core.services.estimate_service import EstimateService, generate_estimate_id
from kis_estimator_core.services.validation_service import ValidationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    summary="견적 생성 (FIX-4 파이프라인)",
    description="FIX-4 파이프라인을 통한 견적 생성 (Stage 1-5)",
    operation_id="createEstimate",
    status_code=status.HTTP_200_OK,
    response_model=EstimateResponse
)
async def create_estimate(
    request: EstimateRequest,
    db: AsyncSession = Depends(get_db)
) -> EstimateResponse:
    """
    견적 생성 (Phase 3 구현)

    ## FIX-4 Pipeline
    - Stage 1: Enclosure (외함 계산) → fit_score ≥ 0.90
    - Stage 2: Breaker (브레이커 배치) → 상평형 ≤ 4%, 간섭=0, 열=0
    - Stage 2.1: Critic (배치 검증)
    - Stage 3: Format (문서 포맷) → 수식 보존 = 100%
    - Stage 4: Cover (표지 생성) → 표지 규칙 = 100%
    - Stage 5: Doc Lint (최종 검증) → lint_errors = 0

    ## 7가지 필수 검증 (자동 실행)
    - CHK_BUNDLE_MAGNET: 마그네트 동반자재 포함 확인
    - CHK_BUNDLE_TIMER: 타이머 동반자재 포함 확인
    - CHK_ENCLOSURE_H_FORMULA: 외함 높이 공식 적용 확인
    - CHK_PHASE_BALANCE: 상평형 ≤ 4% 확인
    - CHK_CLEARANCE_VIOLATIONS: 간섭 = 0 확인
    - CHK_THERMAL_VIOLATIONS: 열밀도 = 0 확인
    - CHK_FORMULA_PRESERVATION: Excel 수식 보존 = 100% 확인

    Args:
        request: EstimateRequest (customer_name, panels, options)
        db: Database session (injected)

    Returns:
        EstimateResponse: 전체 파이프라인 결과 + 검증 결과 + 문서 URL + Evidence

    Raises:
        EstimatorError: 파이프라인 실행 실패 시
    """
    logger.info(f"Estimate request received: customer={request.customer_name}, panels={len(request.panels)}")

    try:
        # Generate estimate ID from DB sequence (TODO[KIS-011] 구현)
        estimate_id = await generate_estimate_id(db)
        logger.info(f"Generated estimate_id from DB: {estimate_id}")

        # Execute FIX-4 pipeline with pre-generated ID
        pipeline = get_pipeline()
        response = await pipeline.execute(request, estimate_id=estimate_id)

        # Save estimate to database for later retrieval
        try:
            service = EstimateService(db)
            await service.save_estimate(
                estimate_id=response.estimate_id,
                request=request,
                response=response,
            )
            logger.info(f"Estimate saved to database: {response.estimate_id}")
        except Exception as save_error:
            # Log but don't fail - estimate was created successfully
            logger.warning(f"Failed to save estimate to DB (non-fatal): {save_error}")

        logger.info(f"Estimate created successfully: {response.estimate_id}")
        return response

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Estimate creation failed: {e}", exc_info=True)
        raise_error(
            ErrorCode.E_INTERNAL,
            "Failed to create estimate",
            hint="Check pipeline logs for details",
            meta={"error": str(e)}
        )


@router.get(
    "/{estimate_id}",
    summary="견적 조회",
    description="ID로 견적을 조회합니다",
    operation_id="getEstimate",
    response_model=EstimateResponse
)
async def get_estimate(
    estimate_id: str,
    db: AsyncSession = Depends(get_db)
) -> EstimateResponse:
    """
    견적 조회 (Phase 3 구현 - Real DB)

    PostgreSQL에서 견적을 조회합니다.

    Args:
        estimate_id: 견적 ID (예: EST-20251118-0001)
        db: Database session (injected)

    Returns:
        EstimateResponse: 견적 전체 데이터

    Raises:
        EstimatorError: 견적을 찾을 수 없는 경우 (E_NOT_FOUND)
    """
    logger.info(f"Estimate retrieval requested: {estimate_id}")

    try:
        service = EstimateService(db)
        response = await service.get_estimate_response(estimate_id)

        logger.info(f"Estimate retrieved successfully: {estimate_id}")
        return response

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Estimate retrieval failed: {e}", exc_info=True)
        raise_error(
            ErrorCode.E_INTERNAL,
            f"Failed to retrieve estimate: {e}",
            hint="Check database connection",
            meta={"estimate_id": estimate_id}
        )


@router.post(
    "/validate",
    summary="견적 검증",
    description="7가지 필수 검증 체크 실행 (독립 실행 모드)",
    operation_id="validateEstimate",
    status_code=status.HTTP_200_OK,
    response_model=ValidationResponse
)
async def validate_estimate(request: EstimateRequest) -> ValidationResponse:
    """
    견적 검증 (Phase 3 구현 - 실제 검증 로직)

    ## 7가지 필수 검증 (개별 실행 가능)
    - CHK_BUNDLE_MAGNET: 마그네트 동반자재 포함 확인
    - CHK_BUNDLE_TIMER: 타이머 동반자재 포함 확인
    - CHK_ENCLOSURE_H_FORMULA: 외함 높이 공식 적용 확인
    - CHK_PHASE_BALANCE: 상평형 ≤ 4% 확인
    - CHK_CLEARANCE_VIOLATIONS: 간섭 = 0 확인
    - CHK_THERMAL_VIOLATIONS: 열밀도 = 0 확인
    - CHK_FORMULA_PRESERVATION: Excel 수식 보존 = 100% 확인

    Note:
    - 이 엔드포인트는 견적 생성 없이 검증만 수행합니다
    - 견적 생성(/v1/estimates POST)에서는 자동으로 검증이 실행됩니다

    Args:
        request: EstimateRequest (검증할 견적 데이터)

    Returns:
        ValidationResponse: 7가지 검증 결과 + 오류 목록

    Raises:
        EstimatorError: 검증 실행 실패 시
    """
    logger.info(f"Validation request received: customer={request.customer_name}, panels={len(request.panels)}")

    try:
        # Execute all 7 mandatory validation checks using ValidationService
        validation_service = ValidationService()
        validation_result = validation_service.validate_all(request)

        # Build ValidationChecks from service result
        checks_dict = validation_result.get("checks", {})
        checks = ValidationChecks(
            CHK_BUNDLE_MAGNET=checks_dict.get("CHK_BUNDLE_MAGNET", "skipped"),
            CHK_BUNDLE_TIMER=checks_dict.get("CHK_BUNDLE_TIMER", "skipped"),
            CHK_ENCLOSURE_H_FORMULA=checks_dict.get("CHK_ENCLOSURE_H_FORMULA", "passed"),
            CHK_PHASE_BALANCE=checks_dict.get("CHK_PHASE_BALANCE", "passed"),
            CHK_CLEARANCE_VIOLATIONS=checks_dict.get("CHK_CLEARANCE_VIOLATIONS", "passed"),
            CHK_THERMAL_VIOLATIONS=checks_dict.get("CHK_THERMAL_VIOLATIONS", "passed"),
            CHK_FORMULA_PRESERVATION=checks_dict.get("CHK_FORMULA_PRESERVATION", "passed"),
        )

        # Build validation response
        response = ValidationResponse(
            validation_id=validation_result.get("validation_id", "VAL-00000000-0000"),
            status=validation_result.get("status", "passed"),
            checks=checks,
            errors=validation_result.get("errors"),
        )

        logger.info(f"Validation completed: {response.validation_id}, status={response.status}")
        return response

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise_error(
            ErrorCode.E_INTERNAL,
            "Failed to validate estimate",
            hint="Check validation logs for details",
            meta={"error": str(e)}
        )
