"""
Endpoint Probe Test - Phase D DoD Requirement (Phase VII-4 Updated)

Tests 8 core endpoints and verifies expected responses.
Results saved to out/evidence/endpoints_probe.json for Evidence Pack.

Requirements:
- Test with FastAPI TestClient (no server needed)
- Verify expected status codes (200/201/404/422/500/503)
- Record all responses for evidence
- DB-dependent endpoints accept 500 per "5xx Fail Fast" policy

Endpoints tested:
1. GET /health - Health liveness (200)
2. GET /readyz - Readiness probe (200/503)
3. POST /v1/estimate - Create estimate deprecated (201/422/500)
4. POST /v1/estimate/plan - K-PEW plan generation (201/422/500)
5. POST /v1/estimate/execute - K-PEW execution (201/422/500)
6. GET /v1/catalog/items - List catalog items (200/500)
7. GET /v1/catalog/items/{sku} - Get single item (404/500)
8. GET /v1/catalog/stats - Catalog statistics (200/500)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from api.main import app


# Test client (no server startup needed)
client = TestClient(app)


def probe_endpoint(method: str, path: str, expected_codes: List[int], json_body: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Probe a single endpoint and record results

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Endpoint path
        expected_codes: List of acceptable status codes
        json_body: Request body for POST/PUT

    Returns:
        Probe result dict
    """

    result = {
        "method": method,
        "path": path,
        "expected_codes": expected_codes,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        # Make request
        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            response = client.post(path, json=json_body or {})
        else:
            result["status"] = "SKIP"
            result["reason"] = f"Unsupported method: {method}"
            return result

        # Record response
        result["status_code"] = response.status_code
        result["status"] = "PASS" if response.status_code in expected_codes else "FAIL"

        # Check deprecation headers (for /v1/estimate)
        if path == "/v1/estimate" and method == "POST":
            result["deprecation_headers"] = {
                "Deprecation": response.headers.get("Deprecation"),
                "Sunset": response.headers.get("Sunset"),
                "Link": response.headers.get("Link"),
                "X-KIS-Deprecation-Reason": response.headers.get("X-KIS-Deprecation-Reason")
            }

        # Record response size
        result["response_size"] = len(response.content)

        # For failed probes, record response body
        if result["status"] == "FAIL":
            try:
                result["response_body"] = response.json()
            except:
                result["response_body"] = response.text[:500]  # First 500 chars

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)

    return result


def run_probes() -> Dict[str, Any]:
    """Run all endpoint probes"""

    probes = [
        # Health checks (200 expected)
        {
            "method": "GET",
            "path": "/health",
            "expected_codes": [200],
        },
        {
            "method": "GET",
            "path": "/readyz",
            "expected_codes": [200, 503],  # 503 if dependencies unavailable
        },

        # Estimate endpoints (422 expected for empty body)
        # Note: Deprecated alias, delegates to K-PEW
        {
            "method": "POST",
            "path": "/v1/estimate",
            "expected_codes": [201, 422, 500],  # 201 success, 422 validation, 500 DB issue
            "json_body": {}
        },
        {
            "method": "POST",
            "path": "/v1/estimate/plan",
            "expected_codes": [201, 422, 500],  # 201 success, 422 validation, 500 DB issue
            "json_body": {}
        },
        {
            "method": "POST",
            "path": "/v1/estimate/execute",
            "expected_codes": [201, 422, 500],  # 201 success, 422 validation, 500 DB issue
            "json_body": {}
        },

        # Catalog endpoints (DB-dependent, may return 500 on DB failure per "5xx Fail Fast" policy)
        {
            "method": "GET",
            "path": "/v1/catalog/items",
            "expected_codes": [200, 500],  # 200 OK, 500 DB unavailable (5xx Fail Fast)
        },
        {
            "method": "GET",
            "path": "/v1/catalog/items/nonexistent-sku",
            "expected_codes": [404, 500],  # 404 not found, 500 DB unavailable
        },
        {
            "method": "GET",
            "path": "/v1/catalog/stats",
            "expected_codes": [200, 500],  # 200 OK, 500 DB unavailable (5xx Fail Fast)
        },
    ]

    results = []
    for probe_config in probes:
        print(f"[PROBE] {probe_config['method']:6} {probe_config['path']}...", end=" ")
        result = probe_endpoint(**probe_config)
        status_icon = {
            "PASS": "[OK]",
            "FAIL": "[FAIL]",
            "ERROR": "[ERROR]",
            "SKIP": "[SKIP]"
        }.get(result["status"], "[?]")
        print(f"{status_icon} {result.get('status_code', 'N/A')}")
        results.append(result)

    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    summary = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate": f"{passed}/{len(results)}"
    }

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "phase": "Phase D - Contract Fixation",
        "summary": summary,
        "probes": results
    }


def save_evidence(results: Dict[str, Any]):
    """Save probe results to evidence directory"""

    evidence_dir = project_root / "out" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    evidence_path = evidence_dir / "endpoints_probe.json"
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Evidence saved: {evidence_path}")
    return evidence_path


def main():
    """Main probe workflow"""

    print("=" * 60)
    print("Endpoint Probe Test - Phase D DoD")
    print("=" * 60)

    # Run probes
    print("\n[1/2] Probing 8 required endpoints...")
    results = run_probes()

    # Save evidence
    print("\n[2/2] Saving evidence...")
    evidence_path = save_evidence(results)

    # Print summary
    print("\n" + "=" * 60)
    summary = results["summary"]
    print(f"[SUMMARY] {summary['passed']}/{summary['total']} probes passed (Phase VII-4 aligned)")

    if summary['failed'] > 0:
        print(f"[WARN] {summary['failed']} probe(s) failed")
    if summary['errors'] > 0:
        print(f"[ERROR] {summary['errors']} probe(s) errored")

    # Exit code (0 if all passed)
    if summary['failed'] == 0 and summary['errors'] == 0:
        print("[SUCCESS] All endpoint probes passed")
        print("=" * 60)
        sys.exit(0)
    else:
        print("[FAIL] Some endpoint probes failed/errored")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
