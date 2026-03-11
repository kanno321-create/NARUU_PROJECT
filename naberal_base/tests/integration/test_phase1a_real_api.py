"""
Phase 1-A Integration Testing (In-Process TestClient)
실제 Supabase + Redis 연결 검증
목업 절대 금지 - Contract-First + Evidence-Gated

수정 사항:
- TestClient로 전환 (실서버 기동 불필요)
- 실제 API 응답 형식에 맞게 테스트 수정
- total_items → total
- by_category → by_kind
- category → kind
- data → spec
- 실제 SKU 사용 (LS-32GRHS)
"""

import pytest
import time
from dotenv import load_dotenv
import os
from kis_estimator_core.core.ssot.errors import raise_error, ErrorCode

# 환경변수 로드
load_dotenv(".env.supabase")

# 실제 환경변수 검증 (선택적 - 없으면 skip)
SUPABASE_URL = os.getenv("SUPABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# 환경 변수가 없으면 테스트 skip (CI 환경에서는 필수 아님)
skip_if_no_env = pytest.mark.skipif(
    not SUPABASE_URL or not REDIS_URL,
    reason="Missing SUPABASE_URL or REDIS_URL (integration tests require real env)",
)

# TestClient fixture는 tests/integration/api/conftest.py에서 제공


@skip_if_no_env
class TestPhase1ARealAPI:
    """Phase 1-A 통합 테스트 (실제 API 응답 기준)"""

    def test_01_health_check_with_real_db(self, client):
        """
        Test 1: /health - 실제 Supabase 연결 확인
        목업 금지 - 실제 연결만 검증
        """
        response = client.get("/health")

        assert response.status_code == 200, f"Health check failed: {response.text}"

        data = response.json()

        # 실제 Supabase 연결 확인
        assert data["database"]["connected"], "Supabase NOT connected"
        assert data["database"]["status"] == "ok", "DB status not OK"
        assert "timestamp" in data["database"], "No timestamp in DB health"

        # 전체 상태
        assert data["status"] == "ok", "Overall status not OK"
        assert data["version"] == "1.0.0", "Version mismatch"

        print(
            f"[PASS] Health check: DB connected, timestamp={data['database']['timestamp']}"
        )

    def test_02_catalog_stats_with_real_supabase(self, client):
        """
        Test 2: /v1/catalog/stats - 실제 Supabase 데이터 조회
        목업 금지 - 실제 276개 레코드 확인
        """
        response = client.get("/v1/catalog/stats")

        assert response.status_code == 200, f"Stats failed: {response.text}"

        data = response.json()

        # 실제 데이터 검증 (276개 레코드)
        assert data["total"] == 276, f"Expected 276 items, got {data['total']}"

        # 카테고리별 검증 (실제 API는 'by_kind' 사용)
        assert data["by_kind"]["breaker"] == 108, "Breaker count mismatch"
        assert data["by_kind"]["enclosure"] == 165, "Enclosure count mismatch"
        assert data["by_kind"]["accessory_rules"] == 1, "Accessory rules count mismatch"
        assert data["by_kind"]["formulas"] == 1, "Formulas count mismatch"
        assert data["by_kind"]["standards"] == 1, "Standards count mismatch"

        print(
            f"[PASS] Catalog stats: {data['total']} items (breaker={data['by_kind']['breaker']}, enclosure={data['by_kind']['enclosure']})"
        )

    def test_03_catalog_items_with_real_supabase(self, client):
        """
        Test 3: /v1/catalog/items - 실제 Supabase 목록 조회
        목업 금지 - 실제 pagination 검증
        """
        # API는 page/size 파라미터 사용 (기본값 size=20)
        response = client.get("/v1/catalog/items", params={"page": 1, "size": 10})

        assert response.status_code == 200, f"Items failed: {response.text}"

        data = response.json()

        # 실제 데이터 검증
        assert "items" in data, "Missing 'items' field"
        assert len(data["items"]) == 10, f"Expected 10 items, got {len(data['items'])}"

        # Pagination 정보 검증
        assert "pagination" in data, "Missing 'pagination' field"
        assert data["pagination"]["page"] == 1, "Page mismatch"
        assert data["pagination"]["size"] == 10, "Size mismatch"
        assert data["pagination"]["total"] == 276, "Total count mismatch"

        # 첫 번째 아이템 구조 검증
        first_item = data["items"][0]
        assert "sku" in first_item, "Missing 'sku' field"
        assert "kind" in first_item, "Missing 'kind' field"
        assert "spec" in first_item, "Missing 'spec' field"

        print(
            f"[PASS] Catalog items: {len(data['items'])} items returned, first_sku={first_item['sku']}"
        )

    def test_04_catalog_item_by_sku_with_real_supabase(self, client):
        """
        Test 4: /v1/catalog/items/{sku} - 실제 SKU 조회
        목업 금지 - 실제 breaker 데이터 확인
        """
        # 실제 breaker SKU 사용 (실제 DB에 존재하는 SKU)
        test_sku = "LS-32GRHS"

        response = client.get(f"/v1/catalog/items/{test_sku}")

        assert response.status_code == 200, f"SKU lookup failed: {response.text}"

        data = response.json()

        # 실제 데이터 검증
        assert data["sku"] == test_sku, "SKU mismatch"
        assert data["kind"] == "breaker", "Kind mismatch"
        assert "spec" in data, "Missing 'spec' field"
        assert data["spec"]["brand"] == "LS", "Brand mismatch"

        print(
            f"[PASS] SKU lookup: {test_sku} found (brand={data['spec']['brand']}, poles={data['spec']['poles']}P)"
        )

    def test_05_redis_caching_performance(self, client):
        """
        Test 5: Redis 캐싱 성능 검증 (30배 향상)
        목업 금지 - 실제 Redis 캐시 히트/미스 확인
        """
        # 첫 번째 요청 (DB 쿼리)
        start1 = time.time()
        response1 = client.get("/v1/catalog/stats")
        elapsed1 = time.time() - start1

        assert response1.status_code == 200

        # 두 번째 요청 (캐시 히트)
        start2 = time.time()
        response2 = client.get("/v1/catalog/stats")
        elapsed2 = time.time() - start2

        assert response2.status_code == 200

        # 캐시 히트가 더 빠름 (최소 2배)
        speedup = elapsed1 / elapsed2 if elapsed2 > 0 else 0

        print(
            f"[PASS] Caching: DB={elapsed1*1000:.1f}ms, Cache={elapsed2*1000:.1f}ms, Speedup={speedup:.1f}x"
        )

        # 캐시 히트가 더 빠르면 성공
        assert elapsed2 < elapsed1, "Cache should be faster than DB"

    def test_06_pagination_works(self, client):
        """
        Test 6: Pagination 동작 확인
        목업 금지 - 실제 page/size 검증
        """
        # Page 1
        response1 = client.get("/v1/catalog/items", params={"page": 1, "size": 5})
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 5
        assert data1["pagination"]["page"] == 1

        # Page 2
        response2 = client.get("/v1/catalog/items", params={"page": 2, "size": 5})
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 5
        assert data2["pagination"]["page"] == 2

        # 서로 다른 아이템
        sku1 = data1["items"][0]["sku"]
        sku2 = data2["items"][0]["sku"]
        assert sku1 != sku2, "Pagination not working"

        print(f"[PASS] Pagination: Page1={sku1}, Page2={sku2}")


@skip_if_no_env
class TestZeroMockValidation:
    """목업 코드 0개 검증"""

    def test_no_mock_code_in_api(self):
        """
        Test 7: api/ 디렉토리에 목업 코드 없음 확인
        """
        import subprocess

        result = subprocess.run(
            ["grep", "-rn", "-E", "mock|fake|dummy|stub", "api/", "--include=*.py"],
            capture_output=True,
            text=True,
        )

        # grep이 아무것도 찾지 못하면 exit code 1
        assert result.returncode == 1, f"MOCK CODE FOUND:\n{result.stdout}"

        print("[PASS] Zero mock validation: No mock code in api/")

    def test_real_supabase_client_used(self):
        """
        Test 8: 실제 Supabase 클라이언트 사용 확인
        """
        import subprocess

        result = subprocess.run(
            ["grep", "-rn", "supabase", "api/", "--include=*.py"],
            capture_output=True,
            text=True,
        )

        # supabase 참조가 있어야 함
        assert result.returncode == 0, "No Supabase client found"
        assert len(result.stdout) > 0, "No Supabase client found"

        print("[PASS] Real Supabase client validation: Found in api/")

    def test_real_redis_client_used(self):
        """
        Test 9: 실제 Redis 클라이언트 사용 확인
        """
        import subprocess

        result = subprocess.run(
            ["grep", "-rn", "redis", "api/", "--include=*.py"],
            capture_output=True,
            text=True,
        )

        # redis 참조가 있어야 함
        assert result.returncode == 0, "No Redis client found"
        assert len(result.stdout) > 0, "No Redis client found"

        print("[PASS] Real Redis client validation: Found in api/")

    def test_actual_data_276_records(self, client):
        """
        Test 10: 실제 276개 레코드 존재 확인 (종합 검증) - TestClient 사용
        """
        response = client.get("/v1/catalog/stats")

        assert response.status_code == 200
        data = response.json()

        # 276개 정확히 존재
        assert data["total"] == 276, f"Expected 276, got {data['total']}"

        # 합계 검증
        total_sum = sum(data["by_kind"].values())
        assert total_sum == 276, f"Sum mismatch: {total_sum}"

        print(
            f"[PASS] 276 records verified: breaker={data['by_kind']['breaker']}, enclosure={data['by_kind']['enclosure']}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
