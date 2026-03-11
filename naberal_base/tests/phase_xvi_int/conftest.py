"""
Phase XVI-B: Public Async API Integration Test Fixtures

SSOT-based fixtures for quote creation payloads
Reuses existing fixtures: db_engine, db_session, http_client
"""

import pytest
import json
from pathlib import Path


@pytest.fixture(scope="session")
def ssot_uom_list():
    """Load SSOT UOM list"""
    uom_path = Path("src/kis_estimator_core/core/ssot/data/uom.json")
    with open(uom_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def ssot_discount_tiers():
    """Load SSOT discount tiers"""
    discount_path = Path("src/kis_estimator_core/core/ssot/data/discount_rules.json")
    with open(discount_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return {tier["tier"]: tier["rate"] for tier in data["tiers"]}


@pytest.fixture(scope="session")
def ssot_approval_threshold():
    """Load SSOT approval threshold (50,000,000 KRW)"""
    discount_path = Path("src/kis_estimator_core/core/ssot/data/discount_rules.json")
    with open(discount_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data["approval_threshold"]["amount"]


@pytest.fixture
def make_quote_payload(ssot_uom_list, ssot_discount_tiers):
    """
    Factory fixture for creating quote payloads with SSOT compliance

    Usage:
        payload = make_quote_payload(
            items=[
                {"sku": "ITEM1", "quantity": 2, "unit_price": 10000, "uom": "EA"},
            ],
            client="TestClient",
            terms_ref="NET30"
        )
    """

    def _make(items=None, client="TestClient", terms_ref="NET30"):
        if items is None:
            # Default: 2 items with different UOMs (EA, M)
            items = [
                {
                    "sku": "BREAKER-SBE-104",
                    "quantity": 2,
                    "unit_price": 15000,
                    "uom": "EA",
                    "discount_tier": "A",  # SSOT: 5%
                },
                {
                    "sku": "BUSBAR-3T15",
                    "quantity": 5,
                    "unit_price": 8000,
                    "uom": "M",
                    "discount_tier": "B",  # SSOT: 8%
                },
            ]

        # Validate UOM
        for item in items:
            if item["uom"] not in ssot_uom_list:
                raise ValueError(f"Invalid UOM: {item['uom']}")
            if "discount_tier" in item and item["discount_tier"]:
                if item["discount_tier"] not in ssot_discount_tiers:
                    raise ValueError(f"Invalid discount_tier: {item['discount_tier']}")

        return {
            "items": items,
            "client": client,
            "terms_ref": terms_ref,
        }

    return _make
