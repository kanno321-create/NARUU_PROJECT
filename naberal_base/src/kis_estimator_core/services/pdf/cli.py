"""CLI interface for PDF estimate generation."""

import json
import sys

from .renderer import render_pdf

if __name__ == "__main__":
    est = json.load(sys.stdin)
    out = render_pdf(
        est,
        "out/pdf/estimate.pdf",
        est.get("_build", "prod-unknown"),
        est.get("_hash", "unknown"),
    )
    print(out)
