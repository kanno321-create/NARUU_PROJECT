"""
Cache TTL Validation Script - Phase VII

카탈로그 캐시 TTL 효과 검증
- 캐시 미스 (첫 번째 요청) vs 캐시 히트 (두 번째 요청)
- TTL: 읽기 900s, 가격 300s
- Evidence: out/evidence/cache_ttl_validation.json
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, List

import httpx


# 테스트 엔드포인트 (Phase VII: TTL 900s for catalog reads)
ENDPOINTS = {
    "catalog_items_breaker": {
        "url": "http://localhost:8000/v1/catalog/items",
        "params": {"kind": "breaker"},
        "ttl": 900,
        "description": "카탈로그 종류별 조회 캐시",
    },
    "catalog_items_search": {
        "url": "http://localhost:8000/v1/catalog/items",
        "params": {"q": "SBE-102"},
        "ttl": 900,
        "description": "카탈로그 검색 캐시",
    },
    "catalog_stats": {
        "url": "http://localhost:8000/v1/catalog/stats",
        "params": {},
        "ttl": 900,
        "description": "카탈로그 통계 캐시",
    },
}

# 반복 횟수
ITERATIONS = 20


async def measure_cache_effect(
    name: str, config: Dict, client: httpx.AsyncClient
) -> Dict:
    """
    캐시 효과 측정 (첫 번째 vs 이후 요청)
    """
    print(f"\n[TESTING] {name} ({config['description']})")
    print(f"   TTL: {config['ttl']}s")
    print(f"   URL: {config['url']}")

    latencies: List[float] = []

    for i in range(ITERATIONS):
        try:
            start = time.perf_counter()
            response = await client.get(
                config["url"],
                params=config.get("params"),
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)

            if i == 0:
                print(f"   [1st] Cache MISS: {elapsed_ms:.2f}ms")
            elif i == 1:
                print(f"   [2nd] Cache HIT:  {elapsed_ms:.2f}ms")

        except Exception as e:
            print(f"   [ERROR] {e}")

    if len(latencies) < 2:
        return {"error": "Not enough measurements"}

    # 첫 번째 (캐시 미스) vs 나머지 (캐시 히트)
    first_request = latencies[0]
    cached_requests = latencies[1:]

    avg_cached = sum(cached_requests) / len(cached_requests)
    improvement = ((first_request - avg_cached) / first_request) * 100

    result = {
        "first_request_ms": first_request,
        "avg_cached_ms": avg_cached,
        "min_cached_ms": min(cached_requests),
        "max_cached_ms": max(cached_requests),
        "improvement_percent": improvement,
        "ttl_seconds": config["ttl"],
        "cache_effective": first_request > avg_cached * 1.2,  # 20% 이상 차이
    }

    print(f"   [RESULTS]")
    print(f"      First (MISS): {result['first_request_ms']:.2f}ms")
    print(f"      Avg (HIT):    {result['avg_cached_ms']:.2f}ms")
    print(f"      Improvement:  {result['improvement_percent']:.1f}%")

    if result["cache_effective"]:
        print("      [CACHE EFFECTIVE] OK")
    else:
        print("      [CACHE NOT EFFECTIVE] WARN")

    return result


async def main():
    """메인 검증 실행"""
    print("=" * 60)
    print("Cache TTL Validation")
    print("Phase VII: 카탈로그 캐시 TTL 효과 검증")
    print("=" * 60)

    results = {}

    async with httpx.AsyncClient() as client:
        for name, config in ENDPOINTS.items():
            result = await measure_cache_effect(name, config, client)
            results[name] = result

    # Evidence 생성
    evidence = {
        "measurement_type": "cache_ttl_validation",
        "phase": "VII",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "iterations": ITERATIONS,
        "endpoints": results,
        "summary": {
            "total_endpoints": len(ENDPOINTS),
            "cache_effective": sum(
                1 for r in results.values() if r.get("cache_effective", False)
            ),
        },
    }

    # Evidence 저장
    evidence_dir = Path("out/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_file = evidence_dir / "cache_ttl_validation.json"

    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    print(f"\n[EVIDENCE] Saved: {evidence_file}")

    # Summary
    print("\n" + "=" * 60)
    print("[SUMMARY]")
    print("=" * 60)

    for name, result in results.items():
        if "error" in result:
            print(f"{name:20s}  [ERROR] {result['error']}")
        else:
            status = "[OK]" if result["cache_effective"] else "[WARN]"
            print(
                f"{name:20s}  "
                f"MISS={result['first_request_ms']:.0f}ms  "
                f"HIT={result['avg_cached_ms']:.0f}ms  "
                f"({result['improvement_percent']:.0f}% improvement)  "
                f"{status}"
            )

    effective_count = evidence["summary"]["cache_effective"]
    total_count = evidence["summary"]["total_endpoints"]

    if effective_count == total_count:
        print(f"\n[SUCCESS] All caches effective ({effective_count}/{total_count})")
        return 0
    else:
        print(f"\n[WARNING] Some caches not effective ({effective_count}/{total_count})")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
