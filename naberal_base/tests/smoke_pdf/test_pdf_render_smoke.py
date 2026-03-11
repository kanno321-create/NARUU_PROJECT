"""Smoke test for PDF render - Zero-Mock, file generation verification."""

import pytest
from pathlib import Path
from kis_estimator_core.services.pdf.renderer import render_pdf


@pytest.mark.smoke
def test_render_pdf_smoke(tmp_path):
    """
    Smoke test: Generate PDF from estimate JSON and verify file creation.

    Zero-Mock: Actually creates PDF file and verifies its existence.
    """
    est = {
        "project": {"title": "HV Switchgear", "client": "KIS Corp"},
        "financial": {"total": 125000000, "currency": "KRW", "vat_pct": 10},
        "dates": {"issued": "2025-10-22", "valid_until": "2025-11-30"},
        "sign": {"prepared_by": "Estimator K"},
        "terms": {
            "payment": "30/40/30",
            "warranty": "Product 1y / Install 6m",
            "lead_time": "4-6 weeks",
        },
        "_build": "prod-20251022",
        "_hash": "abc1234",
    }

    out = render_pdf(est, str(tmp_path / "est.pdf"), est["_build"], est["_hash"])

    # Verify file exists
    assert Path(out).exists(), f"PDF file not created: {out}"

    # Verify file size (should be > 1KB for valid PDF)
    assert (
        Path(out).stat().st_size > 1024
    ), f"PDF file too small: {Path(out).stat().st_size} bytes"


@pytest.mark.smoke
def test_render_pdf_minimal(tmp_path):
    """
    Smoke test: Generate PDF with minimal required fields.

    Tests default value handling.
    """
    est = {
        "project": {"title": "Minimal Test", "client": "Test Client"},
        "financial": {"total": 1000000},
        "dates": {"issued": "2025-10-22", "valid_until": "2025-11-30"},
        "sign": {"prepared_by": "Test User"},
        "terms": {},
        "_build": "test",
        "_hash": "test",
    }

    out = render_pdf(est, str(tmp_path / "minimal.pdf"), "test", "test")

    assert Path(out).exists()
    assert Path(out).stat().st_size > 1024
