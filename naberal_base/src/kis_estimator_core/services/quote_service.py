"""
Quote Service - Phase X Quote Lifecycle & Approval Pack

Responsibilities:
- Save quotes with domain-specific payload (customer, enclosure, breakers, accessories, panels)
- Retrieve quotes by ID
- Approve quotes (internal workflow) with audit trail
- Generate PDF documents (using estimate_formatter pipeline)

BUG-1 재설계: 프론트엔드 도메인 payload를 그대로 저장/반환
- 기존: 제네릭 items (sku, quantity, unit_price, uom) 강제 → 422
- 변경: 도메인 특화 payload 수용 (customer, enclosure, breakers, accessories, panels)

Contract-First / SSOT / Zero-Mock / Evidence-Gated
"""

import hashlib
import json
import logging
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_estimator_core.core.ssot.errors import ErrorCode, EstimatorError, raise_error
from kis_estimator_core.core.ssot.ssot_loader import (
    load_approval_threshold,
    load_rounding,
)
from kis_estimator_core.services.pdf_utils import QuotePDFGenerator
from kis_estimator_core.utils.pdf_auditor import PDFAuditor
from kis_estimator_core.utils.s3_client import get_s3_client

logger = logging.getLogger(__name__)


class QuoteService:
    """
    Quote Lifecycle Service (Phase X)

    BUG-1 재설계: 도메인 특화 payload 수용
    - 프론트엔드에서 보내는 customer/enclosure/breakers/accessories/panels 그대로 저장
    - total_price / total_price_with_vat는 이미 /v1/estimates에서 계산 완료된 값
    - Evidence hash: 전체 payload 기반 SHA256
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._rounding_rules = load_rounding()
        self._approval_threshold = load_approval_threshold()

    def _round_half_up(self, value: float, precision: int = 0) -> int | float:
        """SSOT-compliant rounding (HALF_UP mode)."""
        if precision == 0:
            return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        else:
            quantizer = Decimal(10) ** -precision
            return float(Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP))

    def _extract_client_name(self, customer: Any) -> str:
        """고객 정보에서 표시용 이름 추출 (DB client 컬럼용)"""
        if isinstance(customer, str):
            return customer
        if isinstance(customer, dict):
            return (
                customer.get("name")
                or customer.get("company")
                or customer.get("거래처명")
                or str(customer)
            )
        return str(customer) if customer else ""

    async def create_quote(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        견적 저장 (BUG-1 재설계: 도메인 특화 payload)

        프론트엔드에서 /v1/estimates로 계산 완료 후,
        결과를 DB에 저장하는 persistence 엔드포인트.

        Args:
            payload: {
                "estimate_id": str?,
                "customer": Any,
                "enclosure": dict,
                "main_breakers": list[dict],
                "branch_breakers": list[dict],
                "accessories": list[dict],
                "total_price": float,
                "total_price_with_vat": float,
                "panels": list[dict]
            }

        Returns:
            {
                "quote_id": UUID str,
                "totals": {"subtotal", "discount", "vat", "total", "currency"},
                "approval_required": bool,
                "evidence_hash": str (SHA256),
                "created_at": ISO8601 str
            }
        """
        # 1. Extract fields
        total_price = payload.get("total_price", 0)
        total_price_with_vat = payload.get("total_price_with_vat", 0)
        customer = payload.get("customer", {})

        # 2. Build totals from provided prices
        vat = self._round_half_up(total_price_with_vat - total_price)
        totals = {
            "subtotal": self._round_half_up(total_price),
            "discount": 0,
            "vat": vat,
            "total": self._round_half_up(total_price_with_vat),
            "currency": self._rounding_rules.get("currency", "KRW"),
        }

        # 3. Check approval requirement
        approval_required = self._is_approval_required(totals["total"])

        # 4. Generate evidence hash (full payload)
        evidence_hash = self._generate_evidence_hash(payload)

        # 5. Extract client name for DB column
        client_name = self._extract_client_name(customer)

        # 6. Store in database
        quote_id = uuid4()
        created_at = datetime.now(UTC)

        # items_json stores the FULL domain payload for lossless round-trip
        items_json = json.dumps(payload, default=str, ensure_ascii=False)

        query = text(
            """
            INSERT INTO kis_beta.quotes (
                id, items_json, client, terms_ref, totals_json,
                status, evidence_hash, created_at, updated_at
            ) VALUES (
                :id, :items_json, :client, :terms_ref, :totals_json,
                'DRAFT', :evidence_hash, :created_at, :updated_at
            )
        """
        )

        try:
            await self.db.execute(
                query,
                {
                    "id": str(quote_id),
                    "items_json": items_json,
                    "client": client_name[:200] if client_name else "",
                    "terms_ref": None,
                    "totals_json": json.dumps(totals),
                    "evidence_hash": evidence_hash,
                    "created_at": created_at,
                    "updated_at": created_at,
                },
            )
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create quote: {e}")
            raise_error(ErrorCode.E_INTERNAL, f"Database error: {e}")

        return {
            "quote_id": str(quote_id),
            "totals": totals,
            "approval_required": approval_required,
            "evidence_hash": evidence_hash,
            "created_at": created_at.isoformat(),
        }

    async def get_quote(self, quote_id: str) -> dict[str, Any]:
        """
        Retrieve quote by ID (BUG-1: 도메인 특화 응답)

        items_json에 저장된 도메인 payload를 파싱하여 반환.
        """
        query = text(
            """
            SELECT id, items_json, client, terms_ref, totals_json,
                   status, evidence_hash, created_at, updated_at,
                   approved_at, approved_by
            FROM kis_beta.quotes
            WHERE id = :id
        """
        )

        try:
            result = await self.db.execute(query, {"id": quote_id})
            row = result.fetchone()

            if not row:
                raise_error(ErrorCode.E_NOT_FOUND, f"Quote not found: {quote_id}")

            # Parse stored payload (JSONB auto-parsed by asyncpg, or string from psycopg2)
            raw_payload = row[1]
            if isinstance(raw_payload, str):
                stored_payload = json.loads(raw_payload)
            elif isinstance(raw_payload, (dict, list)):
                stored_payload = raw_payload
            else:
                stored_payload = {}

            # Parse totals
            totals_data = row[4] if isinstance(row[4], dict) else json.loads(row[4]) if row[4] else {}

            # Calculate approval_required
            approval_required = self._is_approval_required(totals_data.get("total", 0))

            # Extract domain fields from stored payload
            # Handles both new format (domain payload) and legacy format (items list)
            if isinstance(stored_payload, dict) and "customer" in stored_payload:
                # New domain payload format
                return {
                    "quote_id": str(row[0]),
                    "estimate_id": stored_payload.get("estimate_id"),
                    "customer": stored_payload.get("customer", {}),
                    "enclosure": stored_payload.get("enclosure", {}),
                    "main_breakers": stored_payload.get("main_breakers", []),
                    "branch_breakers": stored_payload.get("branch_breakers", []),
                    "accessories": stored_payload.get("accessories", []),
                    "panels": stored_payload.get("panels", []),
                    "totals": totals_data,
                    "status": row[5],
                    "approval_required": approval_required,
                    "evidence_hash": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                    "approved_at": row[9].isoformat() if row[9] else None,
                    "approved_by": row[10],
                }
            else:
                # Legacy items-list format (backward compatibility)
                return {
                    "quote_id": str(row[0]),
                    "estimate_id": None,
                    "customer": row[2] or {},
                    "enclosure": {},
                    "main_breakers": [],
                    "branch_breakers": [],
                    "accessories": [],
                    "panels": [],
                    "totals": totals_data,
                    "status": row[5],
                    "approval_required": approval_required,
                    "evidence_hash": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                    "approved_at": row[9].isoformat() if row[9] else None,
                    "approved_by": row[10],
                }
        except EstimatorError:
            raise
        except Exception as e:
            logger.error(f"Failed to get quote: {e}")
            raise_error(ErrorCode.E_INTERNAL, f"Database error: {e}")

    async def approve_quote(
        self, quote_id: str, actor: str, comment: str | None = None
    ) -> dict[str, Any]:
        """
        Approve quote (internal workflow)

        Args:
            quote_id: UUID string
            actor: Approver identifier (email or username)
            comment: Optional approval comment

        Returns:
            {
                "quote_id": str,
                "status": "APPROVED",
                "approved_at": ISO8601 str,
                "approved_by": str,
                "evidence_entry": str (audit log ID)
            }

        Raises:
            AppError E_NOT_FOUND: Quote not found
            AppError E_CONFLICT: Quote already approved or invalid state
            AppError E_INTERNAL: Database error
        """
        # 1. Get current quote
        quote = await self.get_quote(quote_id)

        # 2. Check state
        if quote["status"] == "APPROVED":
            raise_error(
                ErrorCode.E_CONFLICT,
                f"Quote {quote_id} already approved at {quote['approved_at']} by {quote['approved_by']}",
            )

        # 3. Update status
        approved_at = datetime.now(UTC)
        update_query = text(
            """
            UPDATE kis_beta.quotes
            SET status = 'APPROVED',
                approved_at = :approved_at,
                approved_by = :approved_by,
                updated_at = :updated_at
            WHERE id = :id
        """
        )

        # 4. Create audit log entry
        audit_id = uuid4()
        audit_query = text(
            """
            INSERT INTO kis_beta.quote_approval_audit (
                id, quote_id, actor, action, comment,
                old_status, new_status, timestamp
            ) VALUES (
                :id, :quote_id, :actor, 'APPROVE', :comment,
                'DRAFT', 'APPROVED', :timestamp
            )
        """
        )

        try:
            await self.db.execute(
                update_query,
                {
                    "id": quote_id,
                    "approved_at": approved_at,
                    "approved_by": actor,
                    "updated_at": approved_at,
                },
            )
            await self.db.execute(
                audit_query,
                {
                    "id": str(audit_id),
                    "quote_id": quote_id,
                    "actor": actor,
                    "comment": comment,
                    "timestamp": approved_at,
                },
            )
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to approve quote: {e}")
            raise_error(ErrorCode.E_INTERNAL, f"Database error: {e}")

        return {
            "quote_id": quote_id,
            "status": "APPROVED",
            "approved_at": approved_at.isoformat(),
            "approved_by": actor,
            "evidence_entry": f"audit-{audit_id}",
        }

    async def render_pdf(self, quote_id: str) -> dict:
        """
        Generate PDF document for quote (Phase XI)

        Uses QuotePDFGenerator with Evidence Footer + PDF Auditor + S3 Archiving
        """
        # 1. Get quote data
        quote = await self.get_quote(quote_id)

        # 2. Prepare PDF directory
        pdf_dir = Path("out/pdf")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / f"quote-{quote_id}.pdf"

        # 3. Generate PDF with QuotePDFGenerator
        try:
            generator = QuotePDFGenerator()
            generator.generate_quote_pdf(
                quote_data=quote,
                output_path=pdf_path,
            )
            logger.info(f"Generated PDF: {pdf_path}")
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise_error(ErrorCode.E_INTERNAL, f"PDF generation error: {e}")

        # 4. Run PDF auditor (ENFORCED - policy violation = 422)
        auditor = PDFAuditor()
        audit_result = auditor.audit(pdf_path)

        if not audit_result.passed:
            error_summary = "; ".join(audit_result.errors)
            logger.error(f"PDF audit failed: {error_summary}")
            raise_error(
                ErrorCode.E_PDF_POLICY,
                f"PDF policy violation: {error_summary}",
                hint="Check page size (A4), margins (≥10mm), Korean fonts, Evidence Footer",
                meta={
                    "violations": audit_result.errors,
                    "pdf_path": str(pdf_path),
                    "quote_id": quote_id,
                },
            )

        logger.info(f"PDF audit passed: {pdf_path}")

        # 5. S3 archiving (graceful degradation)
        s3_client = get_s3_client()
        s3_upload = s3_client.upload_pdf(
            pdf_path=pdf_path,
            quote_id=quote_id,
            timestamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%S"),
        )

        s3_url = None
        s3_degraded = False
        if s3_upload.success:
            s3_url = s3_upload.s3_url
            logger.info(f"PDF uploaded to S3: {s3_url}")
        else:
            s3_degraded = True
            logger.warning(f"S3 upload failed (degraded mode): {s3_upload.error}")

        # 6. Return result
        approved = quote.get("status") == "APPROVED"

        return {
            "pdf_path": str(pdf_path),
            "evidence_hash": quote["evidence_hash"],
            "approved": approved,
            "audit_passed": audit_result.passed,
            "s3_url": s3_url,
            "s3_degraded": s3_degraded,
        }

    async def get_presigned_url(self, quote_id: str) -> dict[str, Any]:
        """
        Get pre-signed S3 URL for approved quote PDF (Phase XII)
        """
        from kis_estimator_core.core.ssot.constants import S3_URL_TTL_SECONDS

        # 1. Get quote
        quote = await self.get_quote(quote_id)

        # 2. Enforce approval requirement
        if quote["status"] != "APPROVED":
            raise_error(
                ErrorCode.E_VALIDATION,
                f"Quote {quote_id} not approved. Approval required for PDF URL access.",
                hint="Approve quote first: POST /v1/quotes/{id}/approve",
            )

        # 3. Generate pre-signed URL
        s3_client = get_s3_client()
        url, expires_at, storage_mode = s3_client.presign_get_pdf(
            quote_id=quote_id,
            evidence_hash=quote["evidence_hash"],
            ttl=S3_URL_TTL_SECONDS,
        )

        logger.info(
            f"Pre-signed URL generated for {quote_id}: mode={storage_mode}, expires={expires_at}"
        )

        return {
            "url": url,
            "expires_at": expires_at,
            "approved": True,
            "evidence_hash": quote["evidence_hash"],
            "storage_mode": storage_mode,
        }

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _is_approval_required(self, total: float) -> bool:
        """Check if approval is required (SSOT threshold)"""
        threshold: float = float(self._approval_threshold.get("amount", 50000000))
        return total >= threshold

    def _generate_evidence_hash(self, payload: Any) -> str:
        """Generate SHA256 hash of payload for integrity verification"""
        payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
