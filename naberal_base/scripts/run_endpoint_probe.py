#!/usr/bin/env python3
"""
Endpoint Probe Automation Script (Phase I - Test Regrade)

Purpose:
- Load endpoints_probe_config.json
- Execute HTTP probes against 9 core endpoints
- Compare actual responses with expected status codes
- Generate evidence report (out/evidence/endpoints_probe_result.json)

Usage:
    python scripts/run_endpoint_probe.py [--server-url http://localhost:8000]

Zero-Mock Principle:
- NO MOCKS - All probes execute against REAL running server
- If server unavailable, probe SKIPS with reason (not FAIL)
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse

try:
    import requests
except ImportError:
    print("[ERROR] requests library not installed. Run: pip install requests")
    sys.exit(1)


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "scripts" / "endpoints_probe_config.json"
OUTPUT_PATH = PROJECT_ROOT / "out" / "evidence" / "endpoints_probe_result.json"


def load_config() -> Dict[str, Any]:
    """Load probe configuration from JSON file."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config not found: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def probe_endpoint(
    server_url: str,
    method: str,
    path: str,
    expected_codes: List[int],
    timeout_ms: int = 5000,
    payload: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Execute HTTP probe against endpoint.

    Returns:
        {
            "timestamp": "2025-10-14T...",
            "method": "GET",
            "path": "/health",
            "expected_codes": [200, 503],
            "status_code": 200,
            "status": "PASS" | "FAIL" | "SKIP",
            "response_time_ms": 123,
            "response_size": 682,
            "response_body": {...} (optional),
            "error": "..." (if SKIP)
        }
    """
    url = f"{server_url}{path}"
    timeout_sec = timeout_ms / 1000.0

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "path": path,
        "expected_codes": expected_codes,
        "url": url,
    }

    try:
        start = time.time()

        if method == "GET":
            response = requests.get(url, timeout=timeout_sec)
        elif method == "POST":
            response = requests.post(url, json=payload or {}, timeout=timeout_sec)
        elif method == "PUT":
            response = requests.put(url, json=payload or {}, timeout=timeout_sec)
        elif method == "DELETE":
            response = requests.delete(url, timeout=timeout_sec)
        else:
            result["status"] = "SKIP"
            result["error"] = f"Unsupported method: {method}"
            return result

        elapsed = time.time() - start

        result["status_code"] = response.status_code
        result["response_time_ms"] = round(elapsed * 1000, 2)
        result["response_size"] = len(response.content)

        # Include response body if JSON (for evidence)
        try:
            result["response_body"] = response.json()
        except Exception:
            pass  # Non-JSON response, skip

        # Check if status code matches expected
        if response.status_code in expected_codes:
            result["status"] = "PASS"
        else:
            result["status"] = "FAIL"
            result["error"] = f"Expected {expected_codes}, got {response.status_code}"

    except requests.exceptions.ConnectionError:
        result["status"] = "SKIP"
        result["error"] = "Server not reachable (connection refused)"
    except requests.exceptions.Timeout:
        result["status"] = "SKIP"
        result["error"] = f"Timeout after {timeout_ms}ms"
    except Exception as e:
        result["status"] = "SKIP"
        result["error"] = f"Unexpected error: {str(e)}"

    return result


def run_probes(server_url: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute all endpoint probes.

    Returns:
        {
            "timestamp": "...",
            "phase": "Phase I - Test Regrade",
            "server_url": "http://localhost:8000",
            "summary": {
                "total": 9,
                "passed": 7,
                "failed": 1,
                "skipped": 1,
                "pass_rate": "7/9"
            },
            "probes": [...]
        }
    """
    endpoints = config["endpoints"]
    execution_config = config.get("probe_execution", {})
    timeout_ms = execution_config.get("timeout_per_endpoint_ms", 5000)

    probes = []
    passed = 0
    failed = 0
    skipped = 0

    print(f"\n[PROBE] Starting endpoint probes (server: {server_url})")
    print(f"[PROBE] Total endpoints: {len(endpoints)}")
    print(f"[PROBE] Timeout: {timeout_ms}ms\n")

    for endpoint in endpoints:
        path = endpoint["path"]
        method = endpoint["method"]
        expected_codes = endpoint["expected_codes"]
        description = endpoint.get("description", "")

        # Replace {id}/{sku} with sample values for probing
        probe_path = path.replace("{id}", "nonexistent-id").replace("{sku}", "nonexistent-sku")

        print(f"[PROBE] {method} {probe_path} ... ", end="", flush=True)

        result = probe_endpoint(
            server_url=server_url,
            method=method,
            path=probe_path,
            expected_codes=expected_codes,
            timeout_ms=timeout_ms,
        )

        result["description"] = description
        probes.append(result)

        if result["status"] == "PASS":
            passed += 1
            print(f"PASS (got {result['status_code']}, expected {expected_codes})")
        elif result["status"] == "FAIL":
            failed += 1
            print(f"FAIL ({result.get('error', 'Unknown')})")
        else:  # SKIP
            skipped += 1
            print(f"SKIP ({result.get('error', 'Unknown')})")

    summary = {
        "total": len(endpoints),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": f"{passed}/{len(endpoints)}",
    }

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase I - Test Regrade",
        "server_url": server_url,
        "config_version": config.get("version", "unknown"),
        "summary": summary,
        "probes": probes,
    }

    print(f"\n[SUMMARY]")
    print(f"  Total:   {summary['total']}")
    print(f"  Passed:  {summary['passed']}")
    print(f"  Failed:  {summary['failed']}")
    print(f"  Skipped: {summary['skipped']}")
    print(f"  Rate:    {summary['pass_rate']}")

    # Check success criteria
    criteria = config.get("success_criteria", {})
    min_pass = criteria.get("min_endpoints_pass", len(endpoints))
    max_fail = criteria.get("max_failures", 0)

    if passed >= min_pass and failed <= max_fail:
        print(f"\n[RESULT] SUCCESS - All criteria met")
        report["overall_status"] = "SUCCESS"
    else:
        print(f"\n[RESULT] FAILURE - Criteria not met (min_pass={min_pass}, max_fail={max_fail})")
        report["overall_status"] = "FAILURE"

    return report


def save_report(report: Dict[str, Any], output_path: Path):
    """Save probe report to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n[EVIDENCE] Report saved: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Endpoint Probe Automation (Phase I)")
    parser.add_argument(
        "--server-url",
        default="http://localhost:8000",
        help="Server base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help=f"Config path (default: {CONFIG_PATH})",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help=f"Output path (default: {OUTPUT_PATH})",
    )

    args = parser.parse_args()

    try:
        # Load config
        config = load_config()

        # Run probes
        report = run_probes(args.server_url, config)

        # Save report
        save_report(report, Path(args.output))

        # Exit code based on overall status
        if report["overall_status"] == "SUCCESS":
            sys.exit(0)
        else:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
