"""
Phase III: Estimates API Integration Tests

목적: FIX-4 파이프라인 + 7가지 검증 체크 테스트
요구사항:
- POST /v1/estimates: 견적 생성 (FIX-4 pipeline 전체 실행)
- GET /v1/estimates/{id}: 견적 조회 (Phase 3 stub - 404 반환)
- POST /v1/estimates/validate: 독립 검증 (견적 생성 없이 검증만)

엔드포인트:
1. POST /v1/estimates - 견적 생성 (EstimateRequest → EstimateResponse)
2. GET /v1/estimates/{id} - 견적 조회 (stub, 404)
3. POST /v1/estimates/validate - 검증 실행 (EstimateRequest → ValidationResponse)

검증 항목:
- CHK_BUNDLE_MAGNET: 마그네트 동반자재 포함 확인
- CHK_BUNDLE_TIMER: 타이머 동반자재 포함 확인
- CHK_ENCLOSURE_H_FORMULA: 외함 높이 공식 적용 (stub)
- CHK_PHASE_BALANCE: 상평형 ≤ 4% (stub)
- CHK_CLEARANCE_VIOLATIONS: 간섭 = 0 (stub)
- CHK_THERMAL_VIOLATIONS: 열밀도 = 0 (stub)
- CHK_FORMULA_PRESERVATION: 수식 보존 = 100% (stub)

Phase 3 Scope:
- Pydantic 스키마 검증 (EstimateRequest/Response 모델)
- FIX-4 파이프라인 stub 실행 (5 stages)
- 7가지 검증 체크 실행 (magnet/timer는 실제 체크, 나머지는 stub)
- 견적 ID 생성 (EST-YYYYMMDD-NNNN)
- 가격 계산 stub (부가세 포함)
"""

import pytest
from httpx import AsyncClient


# Mark all tests in this module as ssot_api - they require new SSOT API (/v1/estimates)
# not legacy API (/v1/estimate). The test fixture uses legacy api.main app.
# These tests will be excluded from CI until fixture is updated to use SSOT API.
pytestmark = pytest.mark.ssot_api


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_estimate_basic(async_client: AsyncClient):
    """
    POST /v1/estimates - 기본 견적 생성

    요구사항:
    - EstimateRequest Pydantic 검증
    - FIX-4 파이프라인 실행 (5 stages)
    - 7가지 검증 체크
    - EstimateResponse 반환 (estimate_id, pipeline_results, validation_checks, prices)
    """
    # Minimal valid request
    request_data = {
        "customer_name": "테스트 고객사",
        "project_name": "테스트 프로젝트",
        "panels": [
            {
                "panel_name": "분전반1",
                "main_breaker": {
                    "model": "SBE-104",
                    "ampere": 75,
                    "poles": 4,
                    "quantity": 1,
                },
                "branch_breakers": [
                    {"model": "SBE-102", "ampere": 60, "poles": 2, "quantity": 2},
                    {"model": "SEE-102", "ampere": 30, "poles": 2, "quantity": 3},
                ],
                "enclosure": {
                    "type": "옥내노출",
                    "material": "STEEL 1.6T",
                },
            }
        ],
        "options": {
            "breaker_brand_preference": "SANGDO",
            "use_economy_series": True,
            "include_evidence_pack": True,
        },
    }

    response = await async_client.post("/v1/estimates", json=request_data)

    # HTTP 200 OK
    assert response.status_code == 200
    data = response.json()

    # EstimateResponse 필수 필드 검증
    assert "estimate_id" in data
    assert data["estimate_id"].startswith("EST-")  # EST-YYYYMMDD-NNNN
    assert len(data["estimate_id"]) == 17  # EST-20251118-0001

    assert "status" in data
    assert data["status"] in ["completed", "failed", "processing"]

    assert "created_at" in data

    # Pipeline results (5 stages)
    assert "pipeline_results" in data
    pipeline = data["pipeline_results"]
    assert "stage_1_enclosure" in pipeline
    assert "stage_2_breaker" in pipeline
    assert "stage_3_format" in pipeline
    assert "stage_4_cover" in pipeline
    assert "stage_5_doc_lint" in pipeline

    # Stage 1: Enclosure
    stage1 = pipeline["stage_1_enclosure"]
    assert stage1["status"] in ["passed", "failed"]
    assert "fit_score" in stage1
    assert stage1["fit_score"] >= 0.0 and stage1["fit_score"] <= 1.0
    assert "enclosure_size" in stage1
    assert len(stage1["enclosure_size"]) == 3  # [W, H, D]

    # Stage 2: Breaker
    stage2 = pipeline["stage_2_breaker"]
    assert stage2["status"] in ["passed", "failed"]
    assert "phase_balance" in stage2
    assert "clearance_violations" in stage2
    assert "thermal_violations" in stage2

    # Stage 3: Format
    stage3 = pipeline["stage_3_format"]
    assert stage3["status"] in ["passed", "failed"]
    assert "formula_preservation" in stage3

    # Stage 4: Cover
    stage4 = pipeline["stage_4_cover"]
    assert stage4["status"] in ["passed", "failed"]
    assert "cover_compliance" in stage4

    # Stage 5: Doc Lint
    stage5 = pipeline["stage_5_doc_lint"]
    assert stage5["status"] in ["passed", "failed"]
    assert "lint_errors" in stage5

    # Validation checks (7가지)
    assert "validation_checks" in data
    checks = data["validation_checks"]
    assert "CHK_BUNDLE_MAGNET" in checks
    assert "CHK_BUNDLE_TIMER" in checks
    assert "CHK_ENCLOSURE_H_FORMULA" in checks
    assert "CHK_PHASE_BALANCE" in checks
    assert "CHK_CLEARANCE_VIOLATIONS" in checks
    assert "CHK_THERMAL_VIOLATIONS" in checks
    assert "CHK_FORMULA_PRESERVATION" in checks

    # Prices
    assert "total_price" in data
    assert "total_price_with_vat" in data
    assert data["total_price"] > 0
    assert data["total_price_with_vat"] > data["total_price"]

    print(
        f"[OK] Estimate created: {data['estimate_id']}, "
        f"status={data['status']}, "
        f"total={data['total_price']:,}원 (VAT: {data['total_price_with_vat']:,}원)"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_estimate_with_magnet(async_client: AsyncClient):
    """
    POST /v1/estimates - 마그네트 포함 견적

    요구사항:
    - accessories에 magnet 포함
    - CHK_BUNDLE_MAGNET = "passed"
    """
    request_data = {
        "customer_name": "마그네트 테스트 고객",
        "panels": [
            {
                "main_breaker": {
                    "model": "SBE-104",
                    "ampere": 75,
                    "poles": 4,
                    "quantity": 1,
                },
                "branch_breakers": [
                    {"model": "SBE-102", "ampere": 60, "poles": 2, "quantity": 2},
                ],
                "accessories": [
                    {"type": "magnet", "model": "MC-22", "quantity": 2},
                ],
                "enclosure": {
                    "type": "옥내노출",
                    "material": "STEEL 1.6T",
                },
            }
        ],
    }

    response = await async_client.post("/v1/estimates", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # CHK_BUNDLE_MAGNET should be "passed"
    checks = data["validation_checks"]
    assert checks["CHK_BUNDLE_MAGNET"] == "passed"

    print(
        f"[OK] Estimate with magnet: CHK_BUNDLE_MAGNET={checks['CHK_BUNDLE_MAGNET']}"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_estimate_with_timer(async_client: AsyncClient):
    """
    POST /v1/estimates - 타이머 포함 견적

    요구사항:
    - accessories에 timer 포함
    - CHK_BUNDLE_TIMER = "passed"
    """
    request_data = {
        "customer_name": "타이머 테스트 고객",
        "panels": [
            {
                "main_breaker": {
                    "model": "SBE-104",
                    "ampere": 75,
                    "poles": 4,
                    "quantity": 1,
                },
                "branch_breakers": [
                    {"model": "SBE-102", "ampere": 60, "poles": 2, "quantity": 2},
                ],
                "accessories": [
                    {"type": "timer", "model": "ON-DELAY", "quantity": 1},
                ],
                "enclosure": {
                    "type": "옥내노출",
                    "material": "STEEL 1.6T",
                },
            }
        ],
    }

    response = await async_client.post("/v1/estimates", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # CHK_BUNDLE_TIMER should be "passed"
    checks = data["validation_checks"]
    assert checks["CHK_BUNDLE_TIMER"] == "passed"

    print(
        f"[OK] Estimate with timer: CHK_BUNDLE_TIMER={checks['CHK_BUNDLE_TIMER']}"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_estimate_without_accessories(async_client: AsyncClient):
    """
    POST /v1/estimates - 부속자재 없는 견적

    요구사항:
    - accessories 필드 없음 또는 빈 리스트
    - CHK_BUNDLE_MAGNET = "skipped"
    - CHK_BUNDLE_TIMER = "skipped"
    """
    request_data = {
        "customer_name": "부속자재 없는 고객",
        "panels": [
            {
                "main_breaker": {
                    "model": "SBE-104",
                    "ampere": 75,
                    "poles": 4,
                    "quantity": 1,
                },
                "branch_breakers": [
                    {"model": "SBE-102", "ampere": 60, "poles": 2, "quantity": 2},
                ],
                "enclosure": {
                    "type": "옥내노출",
                    "material": "STEEL 1.6T",
                },
            }
        ],
    }

    response = await async_client.post("/v1/estimates", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # CHK_BUNDLE_MAGNET and CHK_BUNDLE_TIMER should be "skipped"
    checks = data["validation_checks"]
    assert checks["CHK_BUNDLE_MAGNET"] == "skipped"
    assert checks["CHK_BUNDLE_TIMER"] == "skipped"

    print(
        f"[OK] Estimate without accessories: "
        f"CHK_BUNDLE_MAGNET={checks['CHK_BUNDLE_MAGNET']}, "
        f"CHK_BUNDLE_TIMER={checks['CHK_BUNDLE_TIMER']}"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_estimate_invalid_breaker_model(async_client: AsyncClient):
    """
    POST /v1/estimates - 유효성 검사 실패 (잘못된 model pattern)

    요구사항:
    - Pydantic 검증 실패 → 422 Unprocessable Entity
    - breaker model pattern: ^(S[BEC][ES]|[AE]B[NS])-?\\d{1,3}[FB]?$
    """
    request_data = {
        "customer_name": "잘못된 모델 테스트",
        "panels": [
            {
                "main_breaker": {
                    "model": "INVALID-MODEL",  # Invalid pattern
                    "ampere": 75,
                    "poles": 4,
                    "quantity": 1,
                },
                "branch_breakers": [
                    {"model": "SBE-102", "ampere": 60, "poles": 2, "quantity": 2},
                ],
                "enclosure": {
                    "type": "옥내노출",
                    "material": "STEEL 1.6T",
                },
            }
        ],
    }

    response = await async_client.post("/v1/estimates", json=request_data)

    # 422 Unprocessable Entity (Pydantic validation error)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

    print("[OK] Invalid breaker model rejected: 422 Unprocessable Entity")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_estimate_returns_404(async_client: AsyncClient):
    """
    GET /v1/estimates/{id} - 견적 조회 (Phase 3 stub)

    요구사항:
    - Phase 3에서는 DB 연동 없이 항상 404 반환
    - TODO[KIS-012]: Phase 4에서 실제 DB 조회 구현
    """
    response = await async_client.get("/v1/estimates/EST-20251118-0001")

    # 404 Not Found (stub implementation)
    assert response.status_code == 404
    data = response.json()

    # SSOT EstimatorError 구조
    assert "code" in data
    assert "message" in data
    assert data["code"] == "E_NOT_FOUND"

    print(
        f"[OK] GET /v1/estimates/{{id}}: 404 (stub), code={data['code']}, message={data['message']}"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_validate_estimate_basic(async_client: AsyncClient):
    """
    POST /v1/estimates/validate - 독립 검증 (기본)

    요구사항:
    - 견적 생성 없이 검증만 수행
    - ValidationResponse 반환 (validation_id, status, checks, errors)
    - 모든 validation checks 실행
    """
    request_data = {
        "customer_name": "검증 테스트 고객",
        "panels": [
            {
                "main_breaker": {
                    "model": "SBE-104",
                    "ampere": 75,
                    "poles": 4,
                    "quantity": 1,
                },
                "branch_breakers": [
                    {"model": "SBE-102", "ampere": 60, "poles": 2, "quantity": 2},
                ],
                "enclosure": {
                    "type": "옥내노출",
                    "material": "STEEL 1.6T",
                },
            }
        ],
    }

    response = await async_client.post("/v1/estimates/validate", json=request_data)

    # HTTP 200 OK
    assert response.status_code == 200
    data = response.json()

    # ValidationResponse 필수 필드
    assert "validation_id" in data
    assert data["validation_id"].startswith("VAL-")  # VAL-YYYYMMDD-NNNN
    assert len(data["validation_id"]) == 17

    assert "status" in data
    assert data["status"] in ["passed", "failed"]

    # Validation checks (7가지)
    assert "checks" in data
    checks = data["checks"]
    assert "CHK_BUNDLE_MAGNET" in checks
    assert "CHK_BUNDLE_TIMER" in checks
    assert "CHK_ENCLOSURE_H_FORMULA" in checks
    assert "CHK_PHASE_BALANCE" in checks
    assert "CHK_CLEARANCE_VIOLATIONS" in checks
    assert "CHK_THERMAL_VIOLATIONS" in checks
    assert "CHK_FORMULA_PRESERVATION" in checks

    # errors (optional)
    # Phase 3 stub: errors=None
    assert "errors" in data

    print(
        f"[OK] Validation completed: {data['validation_id']}, status={data['status']}"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_validate_estimate_with_magnet_and_timer(async_client: AsyncClient):
    """
    POST /v1/estimates/validate - 마그네트 + 타이머 검증

    요구사항:
    - 마그네트와 타이머 모두 포함
    - CHK_BUNDLE_MAGNET = "passed"
    - CHK_BUNDLE_TIMER = "passed"
    """
    request_data = {
        "customer_name": "마그네트+타이머 검증 테스트",
        "panels": [
            {
                "main_breaker": {
                    "model": "SBE-104",
                    "ampere": 75,
                    "poles": 4,
                    "quantity": 1,
                },
                "branch_breakers": [
                    {"model": "SBE-102", "ampere": 60, "poles": 2, "quantity": 2},
                ],
                "accessories": [
                    {"type": "magnet", "model": "MC-22", "quantity": 2},
                    {"type": "timer", "model": "ON-DELAY", "quantity": 1},
                ],
                "enclosure": {
                    "type": "옥내노출",
                    "material": "STEEL 1.6T",
                },
            }
        ],
    }

    response = await async_client.post("/v1/estimates/validate", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # Both checks should be "passed"
    checks = data["checks"]
    assert checks["CHK_BUNDLE_MAGNET"] == "passed"
    assert checks["CHK_BUNDLE_TIMER"] == "passed"

    print(
        f"[OK] Validation with magnet+timer: "
        f"CHK_BUNDLE_MAGNET={checks['CHK_BUNDLE_MAGNET']}, "
        f"CHK_BUNDLE_TIMER={checks['CHK_BUNDLE_TIMER']}"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_estimate_multiple_panels(async_client: AsyncClient):
    """
    POST /v1/estimates - 다중 분전반 견적

    요구사항:
    - panels 배열에 2개 이상 포함
    - 각 panel 독립적으로 처리
    - 전체 견적 하나로 통합
    """
    request_data = {
        "customer_name": "다중 분전반 테스트",
        "project_name": "3층 건물 전기 공사",
        "panels": [
            {
                "panel_name": "1층 분전반",
                "main_breaker": {
                    "model": "SBE-104",
                    "ampere": 75,
                    "poles": 4,
                    "quantity": 1,
                },
                "branch_breakers": [
                    {"model": "SBE-102", "ampere": 60, "poles": 2, "quantity": 2},
                ],
                "enclosure": {
                    "type": "옥내노출",
                    "material": "STEEL 1.6T",
                },
            },
            {
                "panel_name": "2층 분전반",
                "main_breaker": {
                    "model": "SBE-203",
                    "ampere": 175,
                    "poles": 3,
                    "quantity": 1,
                },
                "branch_breakers": [
                    {"model": "SBE-102", "ampere": 60, "poles": 2, "quantity": 3},
                    {"model": "SEE-102", "ampere": 30, "poles": 2, "quantity": 2},
                ],
                "accessories": [
                    {"type": "magnet", "model": "MC-32", "quantity": 1},
                ],
                "enclosure": {
                    "type": "옥내노출",
                    "material": "STEEL 1.6T",
                },
            },
        ],
    }

    response = await async_client.post("/v1/estimates", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # Multiple panels should be processed
    assert data["status"] == "completed"

    # CHK_BUNDLE_MAGNET should be "passed" (2층 분전반에 마그네트 포함)
    checks = data["validation_checks"]
    assert checks["CHK_BUNDLE_MAGNET"] == "passed"

    print(
        f"[OK] Multiple panels estimate created: {data['estimate_id']}, "
        f"total={data['total_price']:,}원"
    )


# ==================== WORK LOG ====================
"""
DECISIONS:
- Phase III: Estimates API 테스트 (FIX-4 pipeline + 7가지 검증)
- Integration tests (AsyncClient + LifespanManager pattern)
- 8개 테스트 케이스 작성
- Zero-Mock: 실제 API 호출, 실제 Pydantic 검증

TEST CASES:
1. test_create_estimate_basic: 기본 견적 생성
2. test_create_estimate_with_magnet: 마그네트 포함
3. test_create_estimate_with_timer: 타이머 포함
4. test_create_estimate_without_accessories: 부속자재 없음 (skipped)
5. test_create_estimate_invalid_breaker_model: Pydantic 검증 실패 (422)
6. test_get_estimate_returns_404: 견적 조회 stub (404)
7. test_validate_estimate_basic: 독립 검증
8. test_validate_estimate_with_magnet_and_timer: 마그네트+타이머 검증
9. test_create_estimate_multiple_panels: 다중 분전반 견적

COVERAGE TARGET:
- api/routes/estimates.py: +15% (3 endpoints)
- engine/fix4_pipeline.py: +12% (FIX4Pipeline class)
- api/schemas/estimates.py: +5% (Pydantic models)

TOTAL EXPECTED: +32% coverage increase

ASSUMPTIONS:
- async_client fixture는 tests/conftest.py에 정의됨
- FIX-4 파이프라인 stub는 정상 작동 (모든 stage "passed" 반환)
- Phase 3 scope: stub 구현만 테스트 (실제 로직은 Phase 5+)
"""
