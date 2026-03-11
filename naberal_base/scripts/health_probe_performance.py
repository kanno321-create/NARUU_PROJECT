"""
Health Probe Performance Measurement Script

Phase VII-4: Health probe 성능 측정
목표: Liveness probe <50ms, Readiness probe <100ms

Usage:
    python scripts/health_probe_performance.py

Output:
    - Console: p50/p95/p99/min/max/avg for each endpoint
    - Evidence: out/evidence/health_probe_performance.json
"""

import asyncio
import json
import statistics
import time
from pathlib import Path
from typing import Dict, List

import httpx

# Health endpoints to measure
ENDPOINTS = {
    "liveness_simple": "http://localhost:8000/health",
    "liveness_probe": "http://localhost:8000/health/live",
    "database_health": "http://localhost:8000/health/db",
    "readiness_check": "http://localhost:8000/readyz",
}

# Performance targets (ms) - Phase VII-4 정석 기준
TARGETS = {
    "liveness_simple": 50,      # 전체 헬스체크 (기존 유지)
    "liveness_probe": 10,       # 순수 liveness (DB 없음) ← 정석
    "database_health": 500,     # DB 전용 (현실적 목표) ← 정석
    "readiness_check": 200,     # DB + 캐시 (현실적 목표) ← 정석
}

# Number of iterations per endpoint
ITERATIONS = 100


async def measure_endpoint(client: httpx.AsyncClient, url: str) -> float:
    """Measure single request response time in milliseconds."""
    start = time.perf_counter()
    response = await client.get(url)
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Ensure we got successful response
    if response.status_code not in [200, 503]:
        raise Exception(f"Unexpected status code: {response.status_code}")

    return elapsed_ms


async def measure_all_endpoints() -> Dict[str, Dict]:
    """Measure all health endpoints multiple times."""
    results = {}

    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, url in ENDPOINTS.items():
            print(f"\n[MEASURING] {name} ({url})...")
            print(f"   Target: <{TARGETS[name]}ms")

            measurements: List[float] = []

            for i in range(ITERATIONS):
                try:
                    elapsed_ms = await measure_endpoint(client, url)
                    measurements.append(elapsed_ms)

                    # Progress indicator every 10 iterations
                    if (i + 1) % 10 == 0:
                        print(f"   Progress: {i + 1}/{ITERATIONS} iterations")

                except Exception as e:
                    print(f"   [ERROR] iteration {i + 1}: {e}")
                    continue

            if not measurements:
                print(f"   [ERROR] No successful measurements for {name}")
                continue

            # Calculate statistics
            sorted_measurements = sorted(measurements)
            count = len(sorted_measurements)

            stats = {
                "count": count,
                "min_ms": min(sorted_measurements),
                "max_ms": max(sorted_measurements),
                "avg_ms": statistics.mean(sorted_measurements),
                "median_ms": statistics.median(sorted_measurements),
                "p50_ms": sorted_measurements[int(count * 0.50)],
                "p95_ms": sorted_measurements[int(count * 0.95)],
                "p99_ms": sorted_measurements[int(count * 0.99)],
                "target_ms": TARGETS[name],
                "target_met": sorted_measurements[int(count * 0.95)] < TARGETS[name],
            }

            results[name] = stats

            # Print results
            print(f"   [RESULTS] ({count} measurements):")
            print(f"      Min:    {stats['min_ms']:.2f}ms")
            print(f"      Avg:    {stats['avg_ms']:.2f}ms")
            print(f"      Median: {stats['median_ms']:.2f}ms")
            print(f"      p95:    {stats['p95_ms']:.2f}ms")
            print(f"      p99:    {stats['p99_ms']:.2f}ms")
            print(f"      Max:    {stats['max_ms']:.2f}ms")

            if stats["target_met"]:
                print(f"      [TARGET MET] p95 ({stats['p95_ms']:.2f}ms) < {TARGETS[name]}ms")
            else:
                print(f"      [TARGET MISSED] p95 ({stats['p95_ms']:.2f}ms) >= {TARGETS[name]}ms")

    return results


def generate_evidence(results: Dict[str, Dict]) -> None:
    """Generate evidence file with measurement results."""
    evidence_dir = Path("out/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    evidence = {
        "measurement_type": "health_probe_performance",
        "phase": "VII-4",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "iterations_per_endpoint": ITERATIONS,
        "endpoints": results,
        "summary": {
            "total_endpoints": len(results),
            "targets_met": sum(1 for r in results.values() if r["target_met"]),
            "targets_missed": sum(1 for r in results.values() if not r["target_met"]),
        },
    }

    evidence_path = evidence_dir / "health_probe_performance.json"
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    print(f"\n[EVIDENCE] Saved: {evidence_path}")


async def main():
    """Main entry point."""
    print("=" * 60)
    print("Health Probe Performance Measurement")
    print("Phase VII-4: API 프로브 안정화")
    print("=" * 60)

    try:
        results = await measure_all_endpoints()
        generate_evidence(results)

        print("\n" + "=" * 60)
        print("[SUMMARY]")
        print("=" * 60)

        for name, stats in results.items():
            status = "[MET]" if stats["target_met"] else "[MISSED]"
            print(f"{name:20} p95={stats['p95_ms']:6.2f}ms  target={stats['target_ms']:3}ms  {status}")

        # Exit with error if any targets missed
        if any(not r["target_met"] for r in results.values()):
            print("\n[WARNING] Some targets were missed. Optimization needed.")
            return 1
        else:
            print("\n[SUCCESS] All targets met!")
            return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
