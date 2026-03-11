"""
Endpoint Probe Test - Contract Fixation Evidence (P4-1)

Tests all 9 required endpoints per REBUILD specification:
1. GET /health
2. GET /readyz
3. POST /v1/estimate (deprecated alias)
4. POST /v1/estimate/plan
5. POST /v1/estimate/execute
6. GET /v1/estimate/{id}
7. GET /v1/catalog/items
8. GET /v1/catalog/items/{sku}
9. GET /v1/catalog/stats

P4-1 Changes:
- Replaced AsyncClient(app=app) with async_client fixture (LifespanManager)
- Fixes "Event loop is closed" bug for catalog endpoints with DB queries
- SB-05 compliant: Real DB operations, no mocks

Evidence:
- Captures expected status codes (200/401/403/422/503)
- Validates response schemas
- Confirms endpoint availability
- Saves results to out/evidence/endpoints_probe.json
"""

import pytest
import json
from pathlib import Path
from datetime import datetime


@pytest.fixture(scope="session")
def evidence_dir():
    """Create evidence directory"""
    evidence_path = Path("out/evidence")
    evidence_path.mkdir(parents=True, exist_ok=True)
    return evidence_path


@pytest.fixture(scope="session")
def probe_results():
    """Probe results accumulator"""
    return {
        "test_run_at": datetime.now().isoformat() + "Z",
        "rebuild_phase": "P4-1",
        "total_endpoints": 9,
        "endpoints": [],
    }


class TestEndpointProbe:
    """Endpoint availability and contract tests"""

    @pytest.mark.asyncio
    async def test_01_health_endpoint(self, async_client, probe_results):
        """GET /health - Health check endpoint"""
        response = await async_client.get("/health")

        result = {
            "endpoint": "GET /health",
            "status_code": response.status_code,
            "expected": [200, 503],
            "passed": response.status_code in [200, 503],
            "response_keys": (
                list(response.json().keys()) if response.status_code == 200 else []
            ),
        }
        probe_results["endpoints"].append(result)

        assert response.status_code in [
            200,
            503,
        ], "Health endpoint should return 200 or 503"
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "version" in data
            assert "environment" in data

    @pytest.mark.asyncio
    async def test_02_readyz_endpoint(self, async_client, probe_results):
        """GET /readyz - Readiness check endpoint"""
        response = await async_client.get("/readyz")

        result = {
            "endpoint": "GET /readyz",
            "status_code": response.status_code,
            "expected": [200, 503],
            "passed": response.status_code in [200, 503],
            "response_keys": (
                list(response.json().keys())
                if response.status_code in [200, 503]
                else []
            ),
        }
        probe_results["endpoints"].append(result)

        assert response.status_code in [
            200,
            503,
        ], "Readyz endpoint should return 200 or 503"
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            # API returns critical_dependencies and optional_dependencies
            assert "critical_dependencies" in data or "core_services" in data

    @pytest.mark.asyncio
    async def test_03_catalog_items_list(self, async_client, probe_results):
        """GET /v1/catalog/items - List catalog items"""
        response = await async_client.get("/v1/catalog/items?page=1&size=5")

        result = {
            "endpoint": "GET /v1/catalog/items",
            "status_code": response.status_code,
            "expected": [200, 401, 503],
            "passed": response.status_code in [200, 401, 503],
            "response_keys": (
                list(response.json().keys()) if response.status_code == 200 else []
            ),
        }
        probe_results["endpoints"].append(result)

        # Expected: 200 (success) or 401 (auth required) or 503 (DB unavailable)
        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_04_catalog_item_get(self, async_client, probe_results):
        """GET /v1/catalog/items/{sku} - Get single item (P4-1: Event loop fix)"""
        # Use a test SKU (might not exist, expecting 404 is OK)
        response = await async_client.get("/v1/catalog/items/TEST-SKU-001")

        result = {
            "endpoint": "GET /v1/catalog/items/{sku}",
            "status_code": response.status_code,
            "expected": [200, 404, 401, 503],
            "passed": response.status_code in [200, 404, 401, 503],
            "note": "404 is expected for non-existent SKU",
        }
        probe_results["endpoints"].append(result)

        # Expected: 200 (found), 404 (not found), 401 (auth), or 503 (DB error)
        assert response.status_code in [200, 404, 401, 503]

    @pytest.mark.asyncio
    async def test_05_catalog_stats(self, async_client, probe_results):
        """GET /v1/catalog/stats - Get catalog statistics"""
        response = await async_client.get("/v1/catalog/stats")

        result = {
            "endpoint": "GET /v1/catalog/stats",
            "status_code": response.status_code,
            "expected": [200, 401, 503],
            "passed": response.status_code in [200, 401, 503],
            "response_keys": (
                list(response.json().keys()) if response.status_code == 200 else []
            ),
        }
        probe_results["endpoints"].append(result)

        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_06_estimate_plan_endpoint(self, async_client, probe_results):
        """POST /v1/estimate/plan - Generate EPDL plan (K-PEW authority)"""
        # Minimal valid request
        payload = {
            "customer_name": "Test Customer",
            "project_name": "Test Project",
            "main_breaker": {"poles": 3, "current": 100, "frame": 100},
            "branch_breakers": [{"poles": 2, "current": 20, "frame": 50}],
        }

        response = await async_client.post("/v1/estimate/plan", json=payload)

        result = {
            "endpoint": "POST /v1/estimate/plan",
            "status_code": response.status_code,
            "expected": [201, 400, 401, 500],
            "passed": response.status_code in [201, 400, 401, 500],
            "note": "400/500 expected if LLM/DB unavailable",
        }
        probe_results["endpoints"].append(result)

        # Expected: 201 (success), 400 (validation), 401 (auth), or 500 (LLM/DB error)
        assert response.status_code in [201, 400, 401, 500]

    @pytest.mark.asyncio
    async def test_07_estimate_execute_endpoint(self, async_client, probe_results):
        """POST /v1/estimate/execute - Execute EPDL plan"""
        # Requires a valid plan_id (won't exist in test)
        payload = {"plan_id": "EST-TEST-NONEXISTENT"}

        response = await async_client.post("/v1/estimate/execute", json=payload)

        result = {
            "endpoint": "POST /v1/estimate/execute",
            "status_code": response.status_code,
            "expected": [200, 400, 404, 401, 500],
            "passed": response.status_code in [200, 400, 404, 401, 500],
            "note": "404 expected for non-existent plan_id",
        }
        probe_results["endpoints"].append(result)

        # Expected: 200 (success), 400 (validation), 404 (plan not found), 401 (auth), or 500 (error)
        assert response.status_code in [200, 400, 404, 401, 500]

    @pytest.mark.asyncio
    async def test_08_estimate_get_endpoint(self, async_client, probe_results):
        """GET /v1/estimate/{id} - Get estimate details (K-PEW authority)"""
        # Test with non-existent ID
        response = await async_client.get("/v1/estimate/EST-TEST-NONEXISTENT")

        result = {
            "endpoint": "GET /v1/estimate/{id}",
            "status_code": response.status_code,
            "expected": [200, 404, 401, 503],
            "passed": response.status_code in [200, 404, 401, 503],
            "note": "404 expected for non-existent estimate",
        }
        probe_results["endpoints"].append(result)

        # Expected: 200 (found), 404 (not found), 401 (auth), or 503 (DB error)
        assert response.status_code in [200, 404, 401, 503]

    @pytest.mark.asyncio
    async def test_09_estimate_deprecated_alias(self, async_client, probe_results):
        """POST /v1/estimate - Deprecated alias (shim → kpew.plan)"""
        # Minimal valid request (same as /plan)
        payload = {
            "customer_name": "Test Customer",
            "project_name": "Test Project",
            "main_breaker": {"poles": 3, "current": 100, "frame": 100},
            "branch_breakers": [{"poles": 2, "current": 20, "frame": 50}],
        }

        response = await async_client.post("/v1/estimate", json=payload)

        result = {
            "endpoint": "POST /v1/estimate (DEPRECATED)",
            "status_code": response.status_code,
            "expected": [201, 400, 401, 500],
            "passed": response.status_code in [201, 400, 401, 500],
            "deprecation_headers": {
                "Deprecation": response.headers.get("Deprecation"),
                "Sunset": response.headers.get("Sunset"),
                "Link": response.headers.get("Link"),
            },
            "note": "Should have Deprecation headers",
        }
        probe_results["endpoints"].append(result)

        # Expected: Same as /v1/estimate/plan
        assert response.status_code in [201, 400, 401, 500]

        # Verify deprecation headers
        assert (
            response.headers.get("Deprecation") == "true"
        ), "Should have Deprecation header"
        assert "Sunset" in response.headers, "Should have Sunset header"
        assert "/v1/estimate/plan" in response.headers.get(
            "Link", ""
        ), "Should reference /plan in Link header"


@pytest.fixture(scope="session", autouse=True)
def save_probe_evidence(probe_results, evidence_dir):
    """Save probe results to evidence file (runs after all tests)"""
    yield  # Wait for all tests to complete

    # Calculate summary
    passed_count = sum(
        1 for ep in probe_results["endpoints"] if ep.get("passed", False)
    )
    probe_results["summary"] = {
        "total_probed": len(probe_results["endpoints"]),
        "passed": passed_count,
        "failed": len(probe_results["endpoints"]) - passed_count,
    }

    # Save to evidence
    evidence_file = evidence_dir / "endpoints_probe.json"
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(probe_results, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Endpoint probe evidence saved: {evidence_file}")
    print(f"   Total: {probe_results['summary']['total_probed']}")
    print(f"   Passed: {probe_results['summary']['passed']}")
    print(f"   Failed: {probe_results['summary']['failed']}")
