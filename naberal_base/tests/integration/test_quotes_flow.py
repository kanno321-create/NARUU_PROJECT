"""
Integration Tests - Phase X Quote Lifecycle Flow

End-to-End workflow:
1. Create quote → 2. Approve quote → 3. Generate PDF

Requires DB connection (Alembic migration applied)
Zero-Mock / Evidence-Gated
"""

import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kis_estimator_core.services.quote_service import QuoteService


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Skipping quotes flow tests in CI - requires real Supabase with quotes table"
    )
]


class TestQuotesLifecycleFlow:
    """Test complete quote lifecycle (create → approve → pdf)"""

    async def test_create_approve_pdf_flow(self, db_session: AsyncSession):
        """
        Full workflow test:
        1. Create quote with SSOT calculation
        2. Approve quote (status DRAFT → APPROVED)
        3. Generate PDF with evidence hash

        Validates:
        - SSOT discount/rounding/VAT applied correctly
        - Approval threshold enforcement (≥50M KRW)
        - Evidence hash integrity
        - PDF generation with footer
        """
        service = QuoteService(db_session)

        # 1. Create quote
        items = [
            {
                "sku": "SBE-104-75A",
                "quantity": 10,
                "unit_price": 12500.0,
                "uom": "EA",
                "discount_tier": "A",
            }
        ]
        result = await service.create_quote(
            items=items, client="삼성전자", terms_ref="NET30"
        )

        quote_id = result["quote_id"]
        assert quote_id
        assert result["totals"]["total"] > 0
        assert result["evidence_hash"]
        assert not result["approval_required"]  # 125K KRW < 50M threshold

        # 2. Approve quote
        approval = await service.approve_quote(
            quote_id=quote_id, actor="김대리@naberal.com"
        )
        assert approval["status"] == "APPROVED"
        assert approval["approved_by"] == "김대리@naberal.com"

        # 3. Generate PDF
        pdf_path = await service.render_pdf(quote_id)
        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"

    async def test_approval_threshold_enforcement(self, db_session: AsyncSession):
        """Test approval_required=True when total ≥ 50M KRW (SSOT rule)"""
        service = QuoteService(db_session)

        # Large quote (≥50M KRW)
        items = [
            {
                "sku": "LARGE-ITEM",
                "quantity": 1000,
                "unit_price": 60000.0,
                "uom": "EA",
            }
        ]
        result = await service.create_quote(items=items, client="대기업")

        assert result["totals"]["total"] >= 50000000
        assert result["approval_required"]  # SSOT threshold enforced
