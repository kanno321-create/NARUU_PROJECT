"""
Quotes Router - Phase X Quote Lifecycle & Approval Pack

Endpoints:
- POST /v1/quotes - Create quote
- GET /v1/quotes/{id} - Get quote
- POST /v1/quotes/{id}/approve - Approve quote
- POST /v1/quotes/{id}/pdf - Generate PDF

Contract-First / SSOT / Zero-Mock / Evidence-Gated / Fail-Fast
"""

import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from kis_estimator_core.services.quote_service import QuoteService
from kis_estimator_core.core.ssot.errors import ErrorCode
from kis_estimator_core.utils.rbac import (
    check_quote_approval_permission,
    check_quote_pdf_permission,
    RBACError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/quotes", tags=["quotes"])


# ============================================================================
# Request/Response Models (Contract-First)
# ============================================================================


class QuoteItemRequest(BaseModel):
    """Quote line item request model"""

    sku: str = Field(..., description="SKU or product code")
    quantity: int = Field(..., gt=0, description="Quantity (must be positive)")
    unit_price: float = Field(..., ge=0, description="Unit price (cannot be negative)")
    uom: str = Field(
        ...,
        description="Unit of measure (validated against SSOT uom.json)",
        pattern="^(EA|SET|M|KG|PCS|BOX|ROLL)$",
    )
    discount_tier: Optional[str] = Field(
        None,
        description="Discount tier (optional, from SSOT discount_rules.json)",
        pattern="^(A|B|VIP|VOLUME|SEASONAL)$",
    )


class CreateQuoteRequest(BaseModel):
    """Create quote request model"""

    items: List[QuoteItemRequest] = Field(
        ..., min_items=1, description="Quote line items (at least 1 required)"
    )
    client: str = Field(..., min_length=1, description="Client name or organization")
    terms_ref: Optional[str] = Field(
        None, description="Payment terms reference (e.g., NET30, NET60)"
    )


class TotalsResponse(BaseModel):
    """Totals calculation response"""

    subtotal: float
    discount: float
    vat: float
    total: float
    currency: str


class CreateQuoteResponse(BaseModel):
    """Create quote response model"""

    quote_id: str
    totals: TotalsResponse
    approval_required: bool
    evidence_hash: str
    created_at: str


class QuoteResponse(BaseModel):
    """Get quote response model"""

    quote_id: str
    items: List[Dict[str, Any]]
    client: str
    terms_ref: Optional[str]
    totals: TotalsResponse
    status: str
    evidence_hash: str
    created_at: str
    updated_at: str
    approved_at: Optional[str]
    approved_by: Optional[str]


class ApprovalRequest(BaseModel):
    """Approve quote request model"""

    actor: str = Field(
        ..., min_length=1, description="Approver identifier (email or username)"
    )
    comment: Optional[str] = Field(None, description="Optional approval comment")


class ApprovalResponse(BaseModel):
    """Approve quote response model"""

    quote_id: str
    status: str
    approved_at: str
    approved_by: str
    evidence_entry: str


# ============================================================================
# Endpoints (Fail-Fast with AppError handling)
# ============================================================================


@router.post(
    "/",
    response_model=CreateQuoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Quote",
    description="""
    Create a new quote with SSOT-based calculation

    SSOT Rules Applied:
    - UOM validation (src/kis_estimator_core/core/ssot/data/uom.json)
    - Discount calculation (src/kis_estimator_core/core/ssot/data/discount_rules.json)
    - Rounding (KRW, precision=0, HALF_UP)
    - VAT 10% applied
    - Approval threshold check (≥50,000,000 KRW → approval_required=true)

    Contract-First / Zero-Mock / Evidence-Gated
    """,
)
async def create_quote(
    req: CreateQuoteRequest,
    db: AsyncSession = Depends(get_db),
) -> CreateQuoteResponse:
    """
    Create quote endpoint (POST /v1/quotes)

    Fail-Fast Error Handling:
    - 422: Validation error (invalid UOM, discount_tier, negative amounts)
    - 500: Internal server error (database failure, unexpected)
    """
    try:
        service = QuoteService(db)
        items_dict = [item.dict() for item in req.items]

        result = await service.create_quote(
            items=items_dict,
            client=req.client,
            terms_ref=req.terms_ref,
        )

        return CreateQuoteResponse(
            quote_id=result["quote_id"],
            totals=TotalsResponse(**result["totals"]),
            approval_required=result["approval_required"],
            evidence_hash=result["evidence_hash"],
            created_at=result["created_at"],
        )

    except Exception as e:
        import uuid
        error_code = getattr(e, "code", None)

        if error_code == ErrorCode.E_VALIDATION:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": error_code,
                    "message": str(e),
                    "hint": "Check SSOT validation (UOM, discount_tier)",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-validation-error", "exception": type(e).__name__},
                },
            )
        else:
            logger.error(f"Unexpected error in create_quote: {e}")
            # 5xx Fail Fast: 즉시 반환, 재시도 없음
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "E_INTERNAL",
                    "message": "Internal server error",
                    "hint": "Check server logs for details",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-create-internal-error", "exception": type(e).__name__},
                },
            )


@router.get(
    "/{quote_id}",
    response_model=QuoteResponse,
    summary="Get Quote",
    description="""
    Retrieve quote by ID

    Returns full quote details including:
    - Items, client, terms_ref
    - Calculated totals
    - Status (DRAFT, APPROVED)
    - Approval metadata (if approved)
    - Evidence hash

    Contract-First / Zero-Mock
    """,
)
async def get_quote(
    quote_id: str,
    db: AsyncSession = Depends(get_db),
) -> QuoteResponse:
    """
    Get quote endpoint (GET /v1/quotes/{id})

    Fail-Fast Error Handling:
    - 404: Quote not found
    - 500: Internal server error
    """
    try:
        service = QuoteService(db)
        result = await service.get_quote(quote_id)

        return QuoteResponse(
            quote_id=result["quote_id"],
            items=result["items"],
            client=result["client"],
            terms_ref=result["terms_ref"],
            totals=TotalsResponse(**result["totals"]),
            status=result["status"],
            evidence_hash=result["evidence_hash"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            approved_at=result.get("approved_at"),
            approved_by=result.get("approved_by"),
        )

    except Exception as e:
        import uuid
        error_code = getattr(e, "code", None)

        if error_code == ErrorCode.E_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": error_code,
                    "message": str(e),
                    "hint": "Check quote_id or use POST /v1/quotes to create new quote",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-not-found", "quote_id": quote_id},
                },
            )
        else:
            logger.error(f"Unexpected error in get_quote: {e}")
            # 5xx Fail Fast: 즉시 반환, 재시도 없음
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "E_INTERNAL",
                    "message": "Internal server error",
                    "hint": "Check server logs and database connection",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-get-internal-error", "exception": type(e).__name__},
                },
            )


@router.post(
    "/{quote_id}/approve",
    response_model=ApprovalResponse,
    summary="Approve Quote",
    description="""
    Approve quote (internal approval workflow)

    RBAC Enforcement (Phase XI):
    - Requires APPROVER role (X-Actor-Role header or JWT claims)
    - Returns 403 if actor does not have APPROVER role

    SSOT Rules:
    - Approval threshold check (from discount_rules.json)
    - Status transition: DRAFT → APPROVED
    - Records: approved_at (TIMESTAMPTZ UTC), approved_by (actor)

    Evidence:
    - Approval audit log entry created
    - Hash verification performed

    Contract-First / Evidence-Gated
    """,
)
async def approve_quote(
    quote_id: str,
    req: ApprovalRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    """
    Approve quote endpoint (POST /v1/quotes/{id}/approve)

    Fail-Fast Error Handling:
    - 403: Insufficient permissions (APPROVER role required)
    - 404: Quote not found
    - 409: Quote already approved or invalid state
    - 500: Internal server error
    """
    # Phase XI: RBAC check (APPROVER role required)
    try:
        check_quote_approval_permission(request)
    except RBACError as e:
        import uuid
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "E_RBAC",
                "message": e.message,
                "hint": "Contact administrator for APPROVER role assignment",
                "required_role": e.required_role,
                "actual_role": e.actual_role,
                "traceId": str(uuid.uuid4()),
                "meta": {"dedupKey": "quote-approval-rbac-error", "quote_id": quote_id},
            },
        )

    try:
        service = QuoteService(db)
        result = await service.approve_quote(
            quote_id=quote_id,
            actor=req.actor,
            comment=req.comment,
        )

        return ApprovalResponse(
            quote_id=result["quote_id"],
            status=result["status"],
            approved_at=result["approved_at"],
            approved_by=result["approved_by"],
            evidence_entry=result["evidence_entry"],
        )

    except Exception as e:
        import uuid
        error_code = getattr(e, "code", None)

        if error_code == ErrorCode.E_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": error_code,
                    "message": str(e),
                    "hint": "Check quote_id or use POST /v1/quotes to create new quote",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-approve-not-found", "quote_id": quote_id},
                },
            )
        elif error_code == ErrorCode.E_CONFLICT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": error_code,
                    "message": str(e),
                    "hint": "Quote already approved or in invalid state for approval",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-approve-conflict", "quote_id": quote_id},
                },
            )
        else:
            logger.error(f"Unexpected error in approve_quote: {e}")
            # 5xx Fail Fast: 즉시 반환, 재시도 없음
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "E_INTERNAL",
                    "message": "Internal server error",
                    "hint": "Check server logs and database connection",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-approve-internal-error", "exception": type(e).__name__},
                },
            )


@router.post(
    "/{quote_id}/pdf",
    summary="Generate Quote PDF",
    description="""
    Generate PDF document for quote (Phase XI)

    RBAC Enforcement (Phase XI):
    - PDF generation only allowed for APPROVED quotes
    - Returns 403 if quote is not APPROVED

    PDF Standard Validation:
    - Font: 맑은고딕 or fallback
    - Paper: A4
    - Margins: 20mm
    - Evidence Footer: Build:[tag] Hash:[8char] Evidence:[hash] TS:[ISO8601]
    - Returns 422 if PDF does not meet standards

    S3 Archiving:
    - PDF uploaded to S3 bucket (if configured)
    - Returns s3_url in response
    - Graceful degradation: X-Archive-Warn header if S3 upload fails

    Contract-First / Evidence-Gated
    """,
    responses={
        200: {
            "content": {"application/json": {}},
            "description": "PDF generated successfully",
        },
        403: {
            "description": "PDF generation forbidden (quote not approved)",
        },
        422: {
            "description": "PDF does not meet standards",
        },
    },
)
async def generate_quote_pdf(
    quote_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Generate PDF endpoint (POST /v1/quotes/{id}/pdf)

    Fail-Fast Error Handling:
    - 403: Quote not approved (RBAC enforcement)
    - 404: Quote not found
    - 422: PDF audit failed (font/margin/footer violations)
    - 500: Internal server error (PDF generation failure)
    """
    # Phase XI: RBAC check (승인 전 PDF 차단)
    try:
        service = QuoteService(db)
        quote = await service.get_quote(quote_id)
        quote_status = quote.get("status")

        check_quote_pdf_permission(request, quote_status)
    except RBACError as e:
        import uuid
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "E_RBAC",
                "message": e.message,
                "hint": "PDF generation only allowed for APPROVED quotes",
                "required_role": e.required_role,
                "actual_role": e.actual_role,
                "traceId": str(uuid.uuid4()),
                "meta": {"dedupKey": "quote-pdf-rbac-error", "quote_id": quote_id},
            },
        )

    try:
        result = await service.render_pdf(quote_id)

        if not result or "path" not in result:
            import uuid
            # 5xx Fail Fast: 즉시 반환, 재시도 없음
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "E_INTERNAL",
                    "message": "PDF generation failed",
                    "hint": "Check PDF generator service and file system",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-pdf-generation-failed", "quote_id": quote_id},
                },
            )

        # Phase XI: S3 archiving (graceful degradation)
        headers = {}
        if result.get("s3_degraded"):
            headers["X-Archive-Warn"] = (
                "S3 archiving unavailable, PDF stored locally only"
            )

        return JSONResponse(
            content={
                "id": quote_id,
                "pdf_path": result["path"],
                "evidence_hash": result.get("evidence_hash"),
                "approved": result.get("approved", False),
                "audit_passed": result.get("audit_passed", False),
                "s3_url": result.get("s3_url"),
            },
            headers=headers,
        )

    except Exception as e:
        import uuid
        from kis_estimator_core.core.ssot.errors import EstimatorError

        # Extract error code from EstimatorError (e.payload.code) or fallback
        error_code = None
        error_hint = None
        if isinstance(e, EstimatorError):
            error_code = e.payload.code
            error_hint = e.payload.hint

        if error_code == ErrorCode.E_NOT_FOUND.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": error_code,
                    "message": str(e),
                    "hint": "Check quote_id or use POST /v1/quotes to create new quote",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-pdf-not-found", "quote_id": quote_id},
                },
            )
        elif error_code == ErrorCode.E_VALIDATION.value:
            # PDF audit failed
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": error_code,
                    "message": str(e),
                    "hint": "PDF validation failed - check audit log",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-pdf-validation-failed", "quote_id": quote_id},
                },
            )
        elif error_code == ErrorCode.E_PDF_POLICY.value:
            # Phase XII: PDF policy violation (422)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": error_code,
                    "message": str(e),
                    "hint": error_hint or "Check page size (A4), margins (≥10mm), Korean fonts, Evidence Footer",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-pdf-policy-violation", "quote_id": quote_id},
                },
            )
        else:
            logger.error(f"Unexpected error in generate_quote_pdf: {e}")
            # 5xx Fail Fast: 즉시 반환, 재시도 없음
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "E_INTERNAL",
                    "message": "Internal server error",
                    "hint": "Check server logs and PDF generation service",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-pdf-internal-error", "exception": type(e).__name__},
                },
            )


@router.get(
    "/{quote_id}/pdf/url",
    summary="Get Pre-signed PDF URL (Phase XII)",
    description="""
    Get pre-signed S3 URL for approved quote PDF

    Requirements:
    - Quote must be APPROVED (403 if not approved)
    - Returns pre-signed URL with 15-minute expiration (SSOT: S3_URL_TTL_SECONDS)
    - Graceful degradation: Returns local:// URL if S3 unavailable

    Headers:
    - X-Storage-Mode: "s3" or "local" (for monitoring)

    RBAC Enforcement:
    - Role: APPROVER or ADMIN required
    - Unapproved quote access → 403

    Contract-First / Evidence-Gated
    """,
    responses={
        200: {
            "content": {"application/json": {}},
            "description": "Pre-signed URL generated successfully",
        },
        403: {
            "description": "Forbidden (quote not approved or insufficient role)",
        },
    },
)
async def get_quote_pdf_url(
    quote_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get pre-signed PDF URL endpoint (GET /v1/quotes/{id}/pdf/url)

    Fail-Fast Error Handling:
    - 403: Quote not approved or insufficient permissions
    - 404: Quote not found
    - 500: Internal server error
    """
    # Phase XII: RBAC check (APPROVER/ADMIN role required)
    try:
        check_quote_approval_permission(request)
    except RBACError as e:
        import uuid
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "E_RBAC",
                "message": e.message,
                "hint": "Contact administrator for APPROVER/ADMIN role assignment",
                "required_role": e.required_role,
                "actual_role": e.actual_role,
                "traceId": str(uuid.uuid4()),
                "meta": {"dedupKey": "quote-url-rbac-error", "quote_id": quote_id},
            },
            headers={"X-Policy-Hint": "Approval required"},
        )

    try:
        service = QuoteService(db)
        result = await service.get_presigned_url(quote_id)

        return JSONResponse(
            content={
                "url": result["url"],
                "expires_at": result["expires_at"],
                "approved": result["approved"],
                "evidence_hash": result["evidence_hash"],
                "storage_mode": result["storage_mode"],
            },
            headers={"X-Storage-Mode": result["storage_mode"]},
        )

    except Exception as e:
        import uuid
        error_code = getattr(e, "code", None)

        if error_code == ErrorCode.E_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": error_code,
                    "message": str(e),
                    "hint": "Check quote_id or generate PDF first: POST /v1/quotes/{id}/pdf",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-url-not-found", "quote_id": quote_id},
                },
            )
        elif error_code == ErrorCode.E_VALIDATION:
            # Quote not approved
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": error_code,
                    "message": str(e),
                    "hint": "Approve quote first: POST /v1/quotes/{id}/approve",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-url-not-approved", "quote_id": quote_id},
                },
                headers={"X-Policy-Hint": "Approval required"},
            )
        else:
            logger.error(f"Unexpected error in get_quote_pdf_url: {e}")
            # 5xx Fail Fast: 즉시 반환, 재시도 없음
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "E_INTERNAL",
                    "message": "Internal server error",
                    "hint": "Check server logs and S3 configuration",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "quote-url-internal-error", "exception": type(e).__name__},
                },
            )
