"""
Quotes Router - Quote Lifecycle API

견적서 생성/조회/승인/PDF 생성 엔드포인트
Contract: spec_kit/api/openapi.yaml#/quotes

Phase X: Quote Lifecycle Implementation
- POST   /v1/quotes           → create_quote()
- GET    /v1/quotes/{id}      → get_quote()
- POST   /v1/quotes/{id}/approve → approve_quote()
- POST   /v1/quotes/{id}/pdf  → render_pdf()
- GET    /v1/quotes/{id}/url  → get_presigned_url()
"""

import logging

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from kis_estimator_core.api.schemas.quotes import (
    QuoteApproveRequest,
    QuoteApproveResponse,
    QuoteCreateRequest,
    QuoteCreateResponse,
    QuoteDetailResponse,
    QuotePDFResponse,
    QuoteURLResponse,
)
from kis_estimator_core.core.ssot.errors import ErrorCode, EstimatorError, raise_error
from kis_estimator_core.infra.db import get_db
from kis_estimator_core.services.quote_service import QuoteService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    summary="Quote 생성",
    description="견적 결과 저장 (도메인 특화 payload: customer/enclosure/breakers/accessories/panels)",
    operation_id="createQuote",
    status_code=status.HTTP_201_CREATED,
    response_model=QuoteCreateResponse,
)
async def create_quote(
    request: QuoteCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> QuoteCreateResponse:
    """
    Quote 생성 (BUG-1 재설계: 도메인 특화 payload)

    /v1/estimates에서 계산 완료된 견적 결과를 DB에 저장하는 persistence 엔드포인트.
    프론트엔드 quote/page.tsx의 handleSaveToDb()에서 호출.
    """
    logger.info("Quote create request received")

    try:
        service = QuoteService(db)
        payload = request.model_dump()
        result = await service.create_quote(payload=payload)

        logger.info(f"Quote created: {result['quote_id']}")

        return QuoteCreateResponse(
            id=result["quote_id"],
            quote_id=result["quote_id"],
            totals=result["totals"],
            approval_required=result["approval_required"],
            evidence_hash=result["evidence_hash"],
            created_at=result["created_at"],
        )

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Quote creation failed: {e}", exc_info=True)
        raise_error(
            ErrorCode.E_INTERNAL,
            "Failed to create quote",
            hint="Check database connection and SSOT configuration",
            meta={"error": str(e)},
        )


@router.get(
    "/{quote_id}",
    summary="Quote 조회",
    description="UUID로 견적서 조회",
    operation_id="getQuote",
    response_model=QuoteDetailResponse,
)
async def get_quote(
    quote_id: str = Path(..., description="Quote UUID"),
    db: AsyncSession = Depends(get_db),
) -> QuoteDetailResponse:
    """
    Quote 조회 (Phase X)

    Args:
        quote_id: UUID string
        db: Database session (injected)

    Returns:
        QuoteDetailResponse: 전체 Quote 정보 (items, totals, status 등)

    Raises:
        EstimatorError E_NOT_FOUND: Quote not found
        EstimatorError E_INTERNAL: Database error
    """
    logger.info(f"Quote get request: {quote_id}")

    try:
        service = QuoteService(db)
        result = await service.get_quote(quote_id)

        logger.info(f"Quote retrieved: {quote_id}, status={result['status']}")

        return QuoteDetailResponse(
            quote_id=result["quote_id"],
            estimate_id=result.get("estimate_id"),
            customer=result.get("customer", {}),
            enclosure=result.get("enclosure", {}),
            main_breakers=result.get("main_breakers", []),
            branch_breakers=result.get("branch_breakers", []),
            accessories=result.get("accessories", []),
            panels=result.get("panels", []),
            totals=result["totals"],
            status=result["status"],
            approval_required=result.get("approval_required", False),
            evidence_hash=result["evidence_hash"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            approved_at=result.get("approved_at"),
            approved_by=result.get("approved_by"),
        )

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Quote retrieval failed: {e}", exc_info=True)
        raise_error(
            ErrorCode.E_INTERNAL,
            f"Failed to retrieve quote: {quote_id}",
            hint="Check database connection",
            meta={"quote_id": quote_id, "error": str(e)},
        )


@router.post(
    "/{quote_id}/approve",
    summary="Quote 승인",
    description="견적서 내부 승인 워크플로우 (DRAFT → APPROVED)",
    operation_id="approveQuote",
    response_model=QuoteApproveResponse,
)
async def approve_quote(
    request: QuoteApproveRequest,
    quote_id: str = Path(..., description="Quote UUID"),
    db: AsyncSession = Depends(get_db),
) -> QuoteApproveResponse:
    """
    Quote 승인 (Phase X)

    ## 워크플로우
    1. Quote 상태 확인 (DRAFT만 승인 가능)
    2. 상태 변경 (DRAFT → APPROVED)
    3. 감사 로그 생성 (quote_approval_audit)

    Args:
        request: QuoteApproveRequest (actor, comment)
        quote_id: UUID string
        db: Database session (injected)

    Returns:
        QuoteApproveResponse: status, approved_at, approved_by, evidence_entry

    Raises:
        EstimatorError E_NOT_FOUND: Quote not found
        EstimatorError E_CONFLICT: Already approved
        EstimatorError E_INTERNAL: Database error
    """
    logger.info(f"Quote approve request: {quote_id}, actor={request.actor}")

    try:
        service = QuoteService(db)
        result = await service.approve_quote(
            quote_id=quote_id,
            actor=request.actor,
            comment=request.comment,
        )

        logger.info(f"Quote approved: {quote_id} by {request.actor}")

        return QuoteApproveResponse(
            quote_id=result["quote_id"],
            status=result["status"],
            approved_at=result["approved_at"],
            approved_by=result["approved_by"],
            evidence_entry=result["evidence_entry"],
        )

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Quote approval failed: {e}", exc_info=True)
        raise_error(
            ErrorCode.E_INTERNAL,
            f"Failed to approve quote: {quote_id}",
            hint="Check database connection and quote status",
            meta={"quote_id": quote_id, "error": str(e)},
        )


@router.post(
    "/{quote_id}/pdf",
    summary="Quote PDF 생성",
    description="견적서 PDF 문서 생성 (Evidence Footer + S3 아카이빙)",
    operation_id="renderQuotePDF",
    response_model=QuotePDFResponse,
)
async def render_quote_pdf(
    quote_id: str = Path(..., description="Quote UUID"),
    db: AsyncSession = Depends(get_db),
) -> QuotePDFResponse:
    """
    Quote PDF 생성 (Phase XI)

    ## PDF 생성 파이프라인
    1. Quote 데이터 조회
    2. QuotePDFGenerator로 PDF 생성
    3. PDFAuditor로 정책 검증 (A4, margin, fonts, footer)
    4. S3 아카이빙 (graceful degradation)

    ## Evidence Footer
    - Build:[tag] Hash:[8char] Evidence:[hash] TS:[ISO8601]

    Args:
        quote_id: UUID string
        db: Database session (injected)

    Returns:
        QuotePDFResponse: pdf_path, evidence_hash, audit_passed, s3_url

    Raises:
        EstimatorError E_NOT_FOUND: Quote not found
        EstimatorError E_PDF_POLICY: PDF policy violation (422)
        EstimatorError E_INTERNAL: PDF generation error
    """
    logger.info(f"Quote PDF render request: {quote_id}")

    try:
        service = QuoteService(db)
        result = await service.render_pdf(quote_id)

        logger.info(f"Quote PDF generated: {result['pdf_path']}")

        return QuotePDFResponse(
            quote_id=quote_id,
            pdf_path=result["pdf_path"],
            evidence_hash=result["evidence_hash"],
            approved=result["approved"],
            audit_passed=result["audit_passed"],
            s3_url=result.get("s3_url"),
            s3_degraded=result.get("s3_degraded", False),
        )

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Quote PDF render failed: {e}", exc_info=True)
        raise_error(
            ErrorCode.E_INTERNAL,
            f"Failed to render PDF: {quote_id}",
            hint="Check PDF generator and S3 configuration",
            meta={"quote_id": quote_id, "error": str(e)},
        )


@router.get(
    "/{quote_id}/url",
    summary="Quote PDF URL 조회",
    description="승인된 견적서 PDF의 Pre-signed URL 조회",
    operation_id="getQuotePDFURL",
    response_model=QuoteURLResponse,
)
async def get_quote_pdf_url(
    quote_id: str = Path(..., description="Quote UUID"),
    db: AsyncSession = Depends(get_db),
) -> QuoteURLResponse:
    """
    Quote PDF Pre-signed URL 조회 (Phase XII)

    ## 요구사항
    - Quote 상태가 APPROVED여야 함
    - S3 사용 불가 시 local:// URL 반환 (graceful degradation)

    Args:
        quote_id: UUID string
        db: Database session (injected)

    Returns:
        QuoteURLResponse: url, expires_at, storage_mode

    Raises:
        EstimatorError E_NOT_FOUND: Quote not found
        EstimatorError E_VALIDATION: Quote not approved (403)
    """
    logger.info(f"Quote PDF URL request: {quote_id}")

    try:
        service = QuoteService(db)
        result = await service.get_presigned_url(quote_id)

        logger.info(f"Quote PDF URL generated: mode={result['storage_mode']}")

        return QuoteURLResponse(
            quote_id=quote_id,
            url=result["url"],
            expires_at=result["expires_at"],
            approved=result["approved"],
            evidence_hash=result["evidence_hash"],
            storage_mode=result["storage_mode"],
        )

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Quote PDF URL failed: {e}", exc_info=True)
        raise_error(
            ErrorCode.E_INTERNAL,
            f"Failed to get PDF URL: {quote_id}",
            hint="Check S3 configuration and quote approval status",
            meta={"quote_id": quote_id, "error": str(e)},
        )
