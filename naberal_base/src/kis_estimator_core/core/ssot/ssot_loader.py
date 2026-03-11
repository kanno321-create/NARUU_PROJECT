"""
SSOT Loader - Phase VII Task 3

UOM(Unit of Measure), Discount Rules, Rounding Rules 로더
모든 상수는 core/ssot/data/*.json에서 로드
"""

import json
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent / "data"


def load_uom() -> list[str]:
    """Load authorized UOM (Unit of Measure) list"""
    return json.loads((BASE / "uom.json").read_text(encoding="utf-8"))


def load_discounts() -> list[dict[str, Any]]:
    """Load discount tier rules (Phase X: returns 'tiers' array from discount_rules.json)"""
    data = json.loads((BASE / "discount_rules.json").read_text(encoding="utf-8"))
    return data.get("tiers", [])


def load_approval_threshold() -> dict[str, Any]:
    """Load approval threshold rules (Phase X: from discount_rules.json)"""
    data = json.loads((BASE / "discount_rules.json").read_text(encoding="utf-8"))
    return data.get("approval_threshold", {"currency": "KRW", "amount": 50000000})


def load_rounding() -> dict[str, Any]:
    """Load rounding rules (currency, precision, mode, VAT)"""
    return json.loads((BASE / "rounding.json").read_text(encoding="utf-8"))
