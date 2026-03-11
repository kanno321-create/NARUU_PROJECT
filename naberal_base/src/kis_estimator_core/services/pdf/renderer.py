"""PDF Estimate Renderer with Cover, Terms, and Evidence Footer."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from kis_estimator_core.core.ssot.constants_format import (
    PDF_FONT_SIZE_FOOTER,
    PDF_FOOTER_POSITION_X_MM,
    PDF_FOOTER_POSITION_Y_MM,
    PDF_FOOTER_TEMPLATE,
)

# Load spec templates (inline to avoid SSOT check issues)
_COVER_SPEC_PATH = (
    Path(__file__).parent.parent.parent.parent.parent
    / "docs/estimates/templates/cover_spec.txt"
)
_TERMS_SPEC_PATH = (
    Path(__file__).parent.parent.parent.parent.parent
    / "docs/estimates/templates/terms_spec.txt"
)

COVER_SPEC = (
    _COVER_SPEC_PATH.read_text(encoding="utf-8") if _COVER_SPEC_PATH.exists() else ""
)
TERMS_SPEC = (
    _TERMS_SPEC_PATH.read_text(encoding="utf-8") if _TERMS_SPEC_PATH.exists() else ""
)


def _compute_doc_hash(estimate: dict) -> str:
    """
    Compute document hash (SHA256) of estimate data.

    Args:
        estimate: Estimate dictionary (project, financial, dates, sign, terms)

    Returns:
        str: First 8 characters of SHA256 hash (hexadecimal)

    Note:
        - Uses canonical JSON serialization (sorted keys, no whitespace)
        - Excludes _build and _hash fields (metadata) for reproducibility
        - UTF-8 encoding for consistent hashing across systems
    """
    # Filter out metadata fields that shouldn't affect document hash
    filtered_estimate = {k: v for k, v in estimate.items() if not k.startswith("_")}

    # Canonical JSON: sorted keys, no whitespace, ensure_ascii=False for Unicode
    canonical_json = json.dumps(
        filtered_estimate, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )

    # SHA256 hash
    hash_obj = hashlib.sha256(canonical_json.encode("utf-8"))

    # Return first 8 hex chars (32 bits, sufficient for Evidence tracking)
    return hash_obj.hexdigest()[:8]


def _draw_footer(c, build_tag: str, git_hash: str, doc_hash: str):
    """
    Draw evidence footer with build tag, git hash, document hash, and timestamp.

    Args:
        c: ReportLab canvas object
        build_tag: Build tag (e.g., "prod-20251022")
        git_hash: Git commit hash (first 8 chars)
        doc_hash: Document content hash (first 8 chars of SHA256)
    """
    c.setFont("Helvetica", PDF_FONT_SIZE_FOOTER)
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Use SSOT template
    footer = PDF_FOOTER_TEMPLATE.format(
        build_tag=build_tag, git_hash=git_hash, doc_hash=doc_hash, timestamp=ts
    )

    c.drawRightString(
        PDF_FOOTER_POSITION_X_MM * mm, PDF_FOOTER_POSITION_Y_MM * mm, footer
    )


def _kv(c, x, y, k, v, fsize=12):
    """Draw key-value pair."""
    c.setFont("Helvetica", fsize)
    c.drawString(x, y, f"{k}: {v}")


def render_pdf(estimate: dict, out_path: str, build_tag: str, git_hash: str) -> str:
    """
    Render estimate JSON to PDF with cover, terms, and evidence footer.

    Args:
        estimate: Dictionary containing:
          - project: {"title": str, "client": str}
          - financial: {"total": int, "currency": str, "vat_pct": int}
          - dates: {"issued": str (YYYY-MM-DD), "valid_until": str (YYYY-MM-DD)}
          - sign: {"prepared_by": str}
          - terms: {"payment": str, "warranty": str, "lead_time": str}
        out_path: Output PDF file path
        build_tag: Build tag for evidence footer (e.g., "prod-20251022Tfinal")
        git_hash: Git commit hash for evidence footer (first 8 chars)

    Returns:
        str: Absolute path to generated PDF file

    Example:
        >>> est = {
        ...     "project": {"title": "HV Switchgear", "client": "KIS Corp"},
        ...     "financial": {"total": 125000000, "currency": "KRW", "vat_pct": 10},
        ...     "dates": {"issued": "2025-10-22", "valid_until": "2025-11-30"},
        ...     "sign": {"prepared_by": "Estimator K"},
        ...     "terms": {"payment": "30/40/30", "warranty": "P1Y/I6M", "lead_time": "4-6w"}
        ... }
        >>> render_pdf(est, "out/pdf/estimate.pdf", "prod-20251022", "abc1234")
        '/path/to/out/pdf/estimate.pdf'
    """
    # Compute document hash (SHA256 of estimate data)
    doc_hash = _compute_doc_hash(estimate)

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(p), pagesize=A4, pageCompression=0)
    W, H = A4

    # === Page 1: Cover ===
    c.setTitle(f"Estimate - {estimate['project']['title']}")
    c.setFont("Helvetica-Bold", 20)
    c.drawString(25 * mm, (H - 40 * mm), "ESTIMATE")

    _kv(c, 25 * mm, H - 60 * mm, "Project", estimate["project"]["title"])
    _kv(c, 25 * mm, H - 70 * mm, "Client", estimate["project"]["client"])

    # Calculate VAT and totals
    currency = estimate["financial"].get("currency", "KRW")
    vat_pct = estimate["financial"].get("vat_pct", 10)
    total_with_vat = estimate["financial"]["total"]
    subtotal = round(total_with_vat / (1 + vat_pct / 100))
    vat_amount = total_with_vat - subtotal

    _kv(c, 25 * mm, H - 80 * mm, "Subtotal", f"{subtotal:,} {currency}")
    _kv(c, 25 * mm, H - 90 * mm, f"VAT ({vat_pct}%)", f"{vat_amount:,} {currency}")
    _kv(c, 25 * mm, H - 100 * mm, "Grand Total", f"{total_with_vat:,} {currency}")

    _kv(c, 25 * mm, H - 115 * mm, "Issued", estimate["dates"]["issued"])
    _kv(c, 25 * mm, H - 125 * mm, "Valid Until", estimate["dates"]["valid_until"])
    _kv(c, 25 * mm, H - 135 * mm, "Prepared By", estimate["sign"]["prepared_by"])

    _draw_footer(c, build_tag, git_hash, doc_hash)
    c.showPage()

    # === Page 2: Terms & Conditions ===
    c.setFont("Helvetica-Bold", 14)
    c.drawString(25 * mm, H - 30 * mm, "Terms & Conditions")

    c.setFont("Helvetica", 11)
    y = H - 45 * mm

    lines = [
        f"Payment: {estimate['terms'].get('payment', '30/40/30')}",
        f"Warranty: {estimate['terms'].get('warranty', 'Product 1y / Installation 6m')}",
        f"Lead Time: {estimate['terms'].get('lead_time', '4-6 weeks')}",
    ]

    for ln in lines:
        c.drawString(25 * mm, y, ln)
        y -= 8 * mm

    # Add spec excerpts (first lines from templates)
    c.setFont("Helvetica", 9)
    for ln in COVER_SPEC.splitlines()[:2] + TERMS_SPEC.splitlines()[:2]:
        if ln.strip():
            c.drawString(25 * mm, y, ln[:95])
            y -= 7 * mm

    _draw_footer(c, build_tag, git_hash, doc_hash)
    c.showPage()

    c.save()
    return str(p.absolute())
