"""Smoke test for PDF evidence footer with build tag, git hash, and timestamp."""

import pytest
from pathlib import Path
from kis_estimator_core.services.pdf.renderer import render_pdf


@pytest.mark.smoke
def test_pdf_footer_contains_build_hash_timestamp(tmp_path):
    """
    Smoke test: Verify PDF footer contains Build, Hash, and TS.

    Zero-Mock: Actually creates PDF and checks for evidence footer text.
    """
    est = {
        "project": {"title": "Footer Test", "client": "Test"},
        "financial": {"total": 1000000, "currency": "KRW", "vat_pct": 10},
        "dates": {"issued": "2025-10-22", "valid_until": "2025-11-30"},
        "sign": {"prepared_by": "Tester"},
        "terms": {},
        "_build": "prod-20251022",
        "_hash": "abc12345",
    }

    out = render_pdf(est, str(tmp_path / "footer.pdf"), "prod-20251022", "abc12345")

    pdf_bytes = Path(out).read_bytes()

    # Check for evidence footer components
    assert b"Build:" in pdf_bytes, "PDF should contain 'Build:' in footer"
    assert b"Hash:" in pdf_bytes, "PDF should contain 'Hash:' in footer"
    assert (
        b"TS:" in pdf_bytes or b"Timestamp" in pdf_bytes
    ), "PDF should contain 'TS:' in footer"

    # Check for actual build tag and hash values
    assert b"prod-20251022" in pdf_bytes, "PDF should contain build tag 'prod-20251022'"
    assert b"abc12345" in pdf_bytes, "PDF should contain git hash 'abc12345'"

    # Check for ISO timestamp format (YYYY-MM-DD)
    assert b"2025-" in pdf_bytes, "PDF should contain year '2025-' in timestamp"


@pytest.mark.smoke
def test_pdf_footer_on_all_pages(tmp_path):
    """
    Smoke test: Verify evidence footer appears on all pages.

    The renderer creates 2 pages (cover + terms), both should have footer.
    """
    est = {
        "project": {"title": "Multi-Page Test", "client": "Test"},
        "financial": {"total": 5000000, "currency": "KRW", "vat_pct": 10},
        "dates": {"issued": "2025-10-22", "valid_until": "2025-11-30"},
        "sign": {"prepared_by": "Tester"},
        "terms": {"payment": "30/40/30", "warranty": "1y", "lead_time": "4w"},
        "_build": "test-multi",
        "_hash": "def67890",
    }

    out = render_pdf(est, str(tmp_path / "multipage.pdf"), "test-multi", "def67890")

    pdf_bytes = Path(out).read_bytes()

    # Footer should appear on both pages
    # Since we call _draw_footer twice (once per showPage), both instances should be in PDF

    # Count occurrences of build tag (should appear at least twice, once per page)
    build_count = pdf_bytes.count(b"test-multi")
    assert (
        build_count >= 2
    ), f"Build tag should appear at least 2 times (found {build_count})"

    # Verify file size suggests 2 pages (larger than single-page PDF)
    assert Path(out).stat().st_size > 2048, "Multi-page PDF should be larger than 2KB"
