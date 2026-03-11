"""
Integration Tests: /v1/estimate API (K-PEW Plan/Execute Architecture)
Stage 1+2+3 통합 테스트 (In-Process TestClient)

Category: INTEGRATION TEST
- Requires database connection
- Full pipeline validation (Stage 1+2+3)
- API routing and quality gates

Skip in CI: requires full pipeline with real Supabase catalog

API Schema (api/routers/kpew.py PlanRequest):
- customer_name: str (required)
- project_name: str (required)
- enclosure_type: str (default: "옥내노출")
- breaker_brand: str (default: "상도차단기")
- main_breaker: BreakerSpec (required) - poles, current, frame
- branch_breakers: List[BreakerSpec] (required)
- accessories: List[Dict] (optional)

BreakerSpec:
- poles: int (2, 3, 4)
- current: int (전류 A)
- frame: int (프레임 AF, must be >= current)
"""

import os
import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Skipping estimate API tests in CI - requires real Supabase catalog"
    )
]

# TestClient fixture는 tests/conftest.py에서 제공


class TestEstimateAPI:
    """견적 API 통합 테스트 (K-PEW Plan Architecture)"""

    def test_api_001_create_estimate_success(self, client):
        """
        INT-API-001: 정상 견적 생성
        - K-PEW Plan 생성
        - VerbSpec 리스트 반환
        """
        request_data = {
            "customer_name": "테스트 고객사",
            "project_name": "테스트 프로젝트",
            "enclosure_type": "옥내노출",
            "breaker_brand": "상도차단기",
            "main_breaker": {
                "poles": 3,
                "current": 100,
                "frame": 100,
            },
            "branch_breakers": [
                {"poles": 3, "current": 20, "frame": 50},
                {"poles": 3, "current": 30, "frame": 50},
            ],
            "accessories": [],
        }

        response = client.post("/v1/estimate", json=request_data)

        # 기본 검증 (201 Created)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        # 필수 필드 검증 (PlanResponse)
        assert "plan_id" in data
        assert data["plan_id"].startswith("EST-")
        assert "estimate_id" in data
        assert "verb_specs" in data
        assert "specs_count" in data
        assert "is_valid" in data
        assert "created_at" in data

        # VerbSpec 검증
        assert data["specs_count"] >= 0
        assert isinstance(data["verb_specs"], list)

        # Deprecation 헤더 확인 (deprecated endpoint)
        assert response.headers.get("Deprecation") == "true"
        assert "Sunset" in response.headers

        print(f"[OK] Plan created: {data['plan_id']}")
        print(f"   - specs_count: {data['specs_count']}")
        print(f"   - is_valid: {data['is_valid']}")

    def test_api_002_missing_required_fields(self, client):
        """
        INT-API-002: 필수 필드 누락 시 422 Validation Error
        - main_breaker 누락
        """
        request_data = {
            "customer_name": "테스트 고객사",
            "project_name": "테스트 프로젝트",
            # main_breaker 누락!
            "branch_breakers": [
                {"poles": 3, "current": 20, "frame": 50},
            ],
        }

        response = client.post("/v1/estimate", json=request_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_api_003_invalid_poles(self, client):
        """
        INT-API-003: 잘못된 극수 (1극 또는 5극)
        - poles는 2, 3, 4만 허용
        """
        request_data = {
            "customer_name": "테스트 고객사",
            "project_name": "테스트 프로젝트",
            "main_breaker": {
                "poles": 1,  # 잘못된 극수
                "current": 100,
                "frame": 100,
            },
            "branch_breakers": [
                {"poles": 3, "current": 20, "frame": 50},
            ],
        }

        response = client.post("/v1/estimate", json=request_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_api_004_frame_less_than_current(self, client):
        """
        INT-API-004: 프레임 < 전류 (비즈니스 규칙 위반)
        - frame은 current 이상이어야 함
        """
        request_data = {
            "customer_name": "테스트 고객사",
            "project_name": "테스트 프로젝트",
            "main_breaker": {
                "poles": 3,
                "current": 100,
                "frame": 50,  # frame < current (잘못됨)
            },
            "branch_breakers": [
                {"poles": 3, "current": 20, "frame": 50},
            ],
        }

        response = client.post("/v1/estimate", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_api_005_performance_target(self, client):
        """
        INT-API-005: 성능 목표 검증
        - 전체 < 5s (최대)
        - 일반적으로 < 2s (목표)
        """
        import time

        request_data = {
            "customer_name": "성능 테스트",
            "project_name": "성능 검증",
            "enclosure_type": "옥내노출",
            "breaker_brand": "상도차단기",
            "main_breaker": {
                "poles": 3,
                "current": 200,
                "frame": 200,
            },
            "branch_breakers": [
                {"poles": 3, "current": 30, "frame": 50} for _ in range(20)
            ],
            "accessories": [],
        }

        start = time.time()
        response = client.post("/v1/estimate", json=request_data)
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 201
        data = response.json()

        # 성능 검증
        assert elapsed_ms < 5000, f"성능 목표 초과: {elapsed_ms}ms > 5000ms"

        # 목표 달성 시 로그
        if elapsed_ms < 2000:
            print(f"성능 목표 달성: {elapsed_ms:.0f}ms < 2000ms")
        else:
            print(f"성능 목표 미달: {elapsed_ms:.0f}ms (목표 2000ms)")

    def test_api_006_get_estimate_not_implemented(self, client):
        """
        INT-API-006: GET /v1/estimate/{id} 조회
        """
        response = client.get("/v1/estimate/EST-20251003000000")

        # K-PEW에서는 404 또는 조회 결과 반환
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestEstimateAPIVariants:
    """견적 API 변형 테스트"""

    def test_variant_001_with_accessories(self, client):
        """
        INT-VAR-001: 부속자재 포함 견적
        """
        request_data = {
            "customer_name": "부속자재 테스트",
            "project_name": "부속자재 검증",
            "main_breaker": {
                "poles": 3,
                "current": 100,
                "frame": 100,
            },
            "branch_breakers": [
                {"poles": 3, "current": 30, "frame": 50},
                {"poles": 3, "current": 30, "frame": 50},
            ],
            "accessories": [
                {"type": "magnet", "model": "MC-32", "quantity": 2},
                {"type": "timer", "model": "24H", "quantity": 1},
            ],
        }

        response = client.post("/v1/estimate", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["is_valid"] is True

    def test_variant_002_large_main_breaker(self, client):
        """
        INT-VAR-002: 대용량 메인 차단기 (800AF)
        """
        request_data = {
            "customer_name": "대용량 테스트",
            "project_name": "800AF 검증",
            "enclosure_type": "옥내자립",
            "main_breaker": {
                "poles": 4,
                "current": 800,
                "frame": 800,
            },
            "branch_breakers": [
                {"poles": 3, "current": 200, "frame": 200},
                {"poles": 3, "current": 200, "frame": 200},
            ],
        }

        response = client.post("/v1/estimate", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert "plan_id" in data

    def test_variant_003_2p_breakers(self, client):
        """
        INT-VAR-003: 2P 차단기 전용 견적
        """
        request_data = {
            "customer_name": "2P 테스트",
            "project_name": "2P 검증",
            "main_breaker": {
                "poles": 2,
                "current": 60,
                "frame": 100,
            },
            "branch_breakers": [
                {"poles": 2, "current": 20, "frame": 30},
                {"poles": 2, "current": 30, "frame": 30},
            ],
        }

        response = client.post("/v1/estimate", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["is_valid"] is True

    def test_variant_004_mixed_poles(self, client):
        """
        INT-VAR-004: 혼합 극수 (2P + 3P)
        """
        request_data = {
            "customer_name": "혼합 극수 테스트",
            "project_name": "혼합 검증",
            "main_breaker": {
                "poles": 3,
                "current": 100,
                "frame": 100,
            },
            "branch_breakers": [
                {"poles": 3, "current": 30, "frame": 50},
                {"poles": 2, "current": 20, "frame": 30},
                {"poles": 3, "current": 50, "frame": 50},
            ],
        }

        response = client.post("/v1/estimate", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["specs_count"] >= 0


@pytest.mark.integration
class TestEstimateAPIEdgeCases:
    """엣지 케이스 테스트"""

    def test_edge_001_empty_branch_breakers(self, client):
        """
        INT-EDGE-001: 분기차단기 없음 (메인만)
        """
        request_data = {
            "customer_name": "메인만 테스트",
            "project_name": "메인만 검증",
            "main_breaker": {
                "poles": 3,
                "current": 100,
                "frame": 100,
            },
            "branch_breakers": [],  # 빈 리스트 (허용됨)
        }

        response = client.post("/v1/estimate", json=request_data)

        # 빈 분기차단기도 허용됨 (min_length=0)
        assert response.status_code == 201

    def test_edge_002_max_branch_breakers(self, client):
        """
        INT-EDGE-002: 많은 분기차단기 (50개)
        """
        request_data = {
            "customer_name": "대량 분기 테스트",
            "project_name": "50개 분기",
            "main_breaker": {
                "poles": 4,
                "current": 400,
                "frame": 400,
            },
            "branch_breakers": [
                {"poles": 3, "current": 30, "frame": 50} for _ in range(50)
            ],
        }

        response = client.post("/v1/estimate", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["specs_count"] >= 0

    def test_edge_003_unicode_customer_name(self, client):
        """
        INT-EDGE-003: 유니코드 고객명
        """
        request_data = {
            "customer_name": "한글주식회사 (주) ㈜",
            "project_name": "테스트 프로젝트 #1 - 가나다",
            "main_breaker": {
                "poles": 3,
                "current": 100,
                "frame": 100,
            },
            "branch_breakers": [
                {"poles": 3, "current": 20, "frame": 50},
            ],
        }

        response = client.post("/v1/estimate", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert "plan_id" in data
