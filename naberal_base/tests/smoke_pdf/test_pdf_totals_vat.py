"""Smoke test for PDF totals and VAT display."""

import pytest
from pathlib import Path
from kis_estimator_core.services.pdf.renderer import render_pdf


@pytest.mark.smoke
def test_pdf_contains_subtotal_vat_grandtotal(tmp_path):
    """
    Smoke test: Verify PDF contains Subtotal, VAT, and Grand Total text.

    Zero-Mock: Actually creates PDF and checks for text presence in bytes.
    """
    est = {
        "project": {"title": "Test Project", "client": "Test Client"},
        "financial": {"total": 110000, "currency": "KRW", "vat_pct": 10},
        "dates": {"issued": "2025-10-22", "valid_until": "2025-11-30"},
        "sign": {"prepared_by": "Tester"},
        "terms": {"payment": "30/40/30", "warranty": "1y", "lead_time": "4w"},
        "_build": "test",
        "_hash": "test",
    }

    out = render_pdf(est, str(tmp_path / "totals.pdf"), "test", "test")

    # Read PDF bytes
    pdf_bytes = Path(out).read_bytes()

    # Check for key text strings (PDF stores text as bytes)
    # Note: Exact match depends on PDF encoding, we check for presence
    assert b"Subtotal" in pdf_bytes, "PDF should contain 'Subtotal'"
    assert b"VAT" in pdf_bytes, "PDF should contain 'VAT'"
    assert b"Grand Total" in pdf_bytes, "PDF should contain 'Grand Total'"

    # Check for currency
    assert b"KRW" in pdf_bytes, "PDF should contain currency 'KRW'"

    # Verify file exists and has reasonable size
    assert Path(out).exists()
    assert Path(out).stat().st_size > 1024


@pytest.mark.smoke
def test_pdf_vat_calculation_correct(tmp_path):
    """
    Smoke test: Verify VAT calculation is correct.

    Total = 110000 KRW (with VAT)
    Subtotal = 100000 KRW
    VAT (10%) = 10000 KRW
    """
    est = {
        "project": {"title": "VAT Test", "client": "Test"},
        "financial": {"total": 110000, "currency": "KRW", "vat_pct": 10},
        "dates": {"issued": "2025-10-22", "valid_until": "2025-11-30"},
        "sign": {"prepared_by": "Tester"},
        "terms": {},
        "_build": "test",
        "_hash": "test",
    }

    out = render_pdf(est, str(tmp_path / "vat_calc.pdf"), "test", "test")

    pdf_bytes = Path(out).read_bytes()

    # Check for calculated values in PDF
    # Subtotal should be 100,000 (formatted with comma)
    # VAT should be 10,000
    # Grand Total should be 110,000

    # Note: PDF encoding may vary, but numbers should be present
    assert (
        b"100,000" in pdf_bytes or b"100000" in pdf_bytes
    ), "Subtotal 100,000 should be in PDF"
    assert (
        b"10,000" in pdf_bytes or b"10000" in pdf_bytes
    ), "VAT 10,000 should be in PDF"
    assert (
        b"110,000" in pdf_bytes or b"110000" in pdf_bytes
    ), "Grand Total 110,000 should be in PDF"
