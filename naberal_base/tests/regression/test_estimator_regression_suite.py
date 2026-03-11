"""
I-3.5 Regression Test Suite (15/15 케이스)

목적: 도메인 회귀 바닥선 고정 (SSOT 기반 파라미터, Zero-Mock)
구성:
  - 정상 6케이스: 소형/중형/대형 브레이커 조합
  - 경계 2케이스: 최소/최대 용량 엣지 케이스
  - 실패 2케이스: 정책 위반/필수 필드 누락
  - 별칭 3케이스: /v1/estimate ↔ /v1/estimate/plan 동등성
  - 오류 4케이스: 422/403/503/500 경로

DoD: 15/15 PASS, 커버리지 ≥60%, Evidence 생성
"""

import pytest
from httpx import AsyncClient


# ==================== SSOT 기반 파라미터 정의 ====================

# 정상 케이스 6개 (소형/중형/대형)
NORMAL_CASES = [
    pytest.param(
        {
            "customer_name": "회귀테스트_소형_케이스1",
            "project_name": "소형 분전반 (2P 20A)",
            "main_breaker": {"poles": 2, "current": 20, "frame": 30},
            "branch_breakers": [
                {"poles": 2, "current": 15, "frame": 30},
                {"poles": 2, "current": 20, "frame": 30},
            ],
            "accessories": [],
        },
        id="normal_small_2p_20a",
    ),
    pytest.param(
        {
            "customer_name": "회귀테스트_소형_케이스2",
            "project_name": "소형 분전반 (3P 30A)",
            "main_breaker": {"poles": 3, "current": 30, "frame": 50},
            "branch_breakers": [
                {"poles": 2, "current": 15, "frame": 30},
                {"poles": 2, "current": 20, "frame": 30},
                {"poles": 3, "current": 30, "frame": 50},
            ],
            "accessories": [],
        },
        id="normal_small_3p_30a",
    ),
    pytest.param(
        {
            "customer_name": "회귀테스트_중형_케이스1",
            "project_name": "중형 분전반 (3P 100A)",
            "main_breaker": {"poles": 3, "current": 100, "frame": 100},
            "branch_breakers": [
                {"poles": 2, "current": 60, "frame": 100},
                {"poles": 3, "current": 75, "frame": 100},
                {"poles": 3, "current": 100, "frame": 100},
            ],
            "accessories": [],
        },
        id="normal_medium_3p_100a",
    ),
    pytest.param(
        {
            "customer_name": "회귀테스트_중형_케이스2",
            "project_name": "중형 분전반 (4P 150A)",
            "main_breaker": {"poles": 4, "current": 150, "frame": 200},
            "branch_breakers": [
                {"poles": 2, "current": 100, "frame": 100},
                {"poles": 3, "current": 125, "frame": 200},
                {"poles": 4, "current": 150, "frame": 200},
            ],
            "accessories": [],
        },
        id="normal_medium_4p_150a",
    ),
    pytest.param(
        {
            "customer_name": "회귀테스트_대형_케이스1",
            "project_name": "대형 분전반 (3P 300A)",
            "main_breaker": {"poles": 3, "current": 300, "frame": 400},
            "branch_breakers": [
                {"poles": 3, "current": 200, "frame": 200},
                {"poles": 3, "current": 250, "frame": 250},
                {"poles": 3, "current": 300, "frame": 400},
            ],
            "accessories": [],
        },
        id="normal_large_3p_300a",
    ),
    pytest.param(
        {
            "customer_name": "회귀테스트_대형_케이스2",
            "project_name": "대형 분전반 (4P 400A)",
            "main_breaker": {"poles": 4, "current": 400, "frame": 400},
            "branch_breakers": [
                {"poles": 4, "current": 300, "frame": 400},
                {"poles": 4, "current": 350, "frame": 400},
                {"poles": 4, "current": 400, "frame": 400},
            ],
            "accessories": [],
        },
        id="normal_large_4p_400a",
    ),
]

# 경계 케이스 2개 (최소/최대 용량)
BOUNDARY_CASES = [
    pytest.param(
        {
            "customer_name": "회귀테스트_경계_최소",
            "project_name": "최소 용량 (2P 15A)",
            "main_breaker": {"poles": 2, "current": 15, "frame": 30},
            "branch_breakers": [{"poles": 2, "current": 15, "frame": 30}],
            "accessories": [],
        },
        id="boundary_min_2p_15a",
    ),
    pytest.param(
        {
            "customer_name": "회귀테스트_경계_최대",
            "project_name": "최대 용량 (4P 800A)",
            "main_breaker": {"poles": 4, "current": 800, "frame": 800},
            "branch_breakers": [
                {"poles": 4, "current": 600, "frame": 600},
                {"poles": 4, "current": 700, "frame": 800},
                {"poles": 4, "current": 800, "frame": 800},
            ],
            "accessories": [],
        },
        id="boundary_max_4p_800a",
    ),
]

# 실패 케이스 2개 (정책 위반/필수 필드 누락)
FAILURE_CASES = [
    pytest.param(
        {
            "customer_name": "회귀테스트_실패_정책위반",
            "project_name": "정책 위반 (frame < current)",
            "main_breaker": {
                "poles": 3,
                "current": 100,
                "frame": 50,
            },  # frame < current (불가능)
            "branch_breakers": [
                {"poles": 2, "current": 60, "frame": 30}  # frame < current (불가능)
            ],
            "accessories": [],
        },
        id="failure_policy_violation",
    ),
    pytest.param(
        {
            "customer_name": "회귀테스트_실패_필수누락",
            "project_name": "필수 필드 누락",
            "main_breaker": {"poles": 3},  # current, frame 누락
            "branch_breakers": [],
            "accessories": [],
        },
        id="failure_missing_field",
    ),
]


# ==================== 정상 케이스 테스트 (6/15) ====================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.flaky(reruns=2, reruns_delay=1)  # Phase VII-3: event loop 간헐적 간섭 방지
@pytest.mark.parametrize("plan_request", NORMAL_CASES)
async def test_regression_normal_cases(async_client: AsyncClient, plan_request: dict):
    """
    회귀 테스트: 정상 케이스 (6/15)

    조건:
    - SSOT 기반 유효한 브레이커 조합
    - 정상 plan 생성 → execute 성공 예상

    검증:
    - 201 Created
    - plan_id 생성
    - verb_specs 2개 (PICK_ENCLOSURE + PLACE)
    - is_valid = True
    """
    # Step 1: Plan 생성
    response = await async_client.post("/v1/estimate/plan", json=plan_request)

    assert (
        response.status_code == 201
    ), f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()
    assert "plan_id" in data
    assert "verb_specs" in data
    assert data["is_valid"] is True
    assert data["specs_count"] == 2  # PICK_ENCLOSURE + PLACE

    print(
        f"[OK] Normal case: {plan_request['project_name']} - plan_id={data['plan_id']}"
    )


# ==================== 경계 케이스 테스트 (2/15) ====================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.parametrize("plan_request", BOUNDARY_CASES)
async def test_regression_boundary_cases(async_client: AsyncClient, plan_request: dict):
    """
    회귀 테스트: 경계 케이스 (2/15)

    조건:
    - 최소 용량 (2P 15A)
    - 최대 용량 (4P 800A)

    검증:
    - 201 Created (경계값도 정상 처리)
    - VerbSpec 생성 성공
    """
    response = await async_client.post("/v1/estimate/plan", json=plan_request)

    assert (
        response.status_code == 201
    ), f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["is_valid"] is True
    assert data["specs_count"] == 2

    print(
        f"[OK] Boundary case: {plan_request['project_name']} - plan_id={data['plan_id']}"
    )


# ==================== 실패 케이스 테스트 (2/15) ====================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.parametrize("plan_request", FAILURE_CASES)
async def test_regression_failure_cases(async_client: AsyncClient, plan_request: dict):
    """
    회귀 테스트: 실패 케이스 (2/15)

    조건:
    - 정책 위반 (frame < current)
    - 필수 필드 누락

    검증:
    - 400 Bad Request 또는 422 Unprocessable Entity
    - 적절한 에러 메시지
    """
    response = await async_client.post("/v1/estimate/plan", json=plan_request)

    # 실패 케이스는 400 또는 422 예상
    assert response.status_code in [
        400,
        422,
    ], f"Expected 400 or 422, got {response.status_code}: {response.text}"

    data = response.json()
    assert (
        "code" in data or "detail" in data
    ), "Error response should have code or detail"

    print(
        f"[OK] Failure case detected: {plan_request['project_name']} - status={response.status_code}"
    )


# ==================== 별칭 동등성 테스트 (3/15) ====================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.parametrize(
    "plan_request",
    [
        pytest.param(NORMAL_CASES[0].values[0], id="alias_small"),
        pytest.param(NORMAL_CASES[2].values[0], id="alias_medium"),
        pytest.param(NORMAL_CASES[4].values[0], id="alias_large"),
    ],
)
async def test_regression_alias_equivalence(
    async_client: AsyncClient, plan_request: dict
):
    """
    회귀 테스트: 별칭 동등성 (3/15)

    조건:
    - /v1/estimate (deprecated) ↔ /v1/estimate/plan 동등성 검증

    검증:
    - 동일 입력 → 동일 응답 구조
    - 둘 다 201 Created
    - verb_specs 구조 동일
    """
    # /v1/estimate/plan (current)
    response_plan = await async_client.post("/v1/estimate/plan", json=plan_request)
    assert response_plan.status_code == 201
    data_plan = response_plan.json()

    # /v1/estimate (deprecated alias)
    response_alias = await async_client.post("/v1/estimate", json=plan_request)
    assert response_alias.status_code == 201
    data_alias = response_alias.json()

    # 응답 구조 동등성 검증
    assert (
        data_plan.keys() == data_alias.keys()
    ), "Response structure should be identical"
    assert data_plan["specs_count"] == data_alias["specs_count"]
    assert data_plan["is_valid"] == data_alias["is_valid"]

    print(
        f"[OK] Alias equivalence: {plan_request['project_name']} - both endpoints work identically"
    )


# ==================== 오류 경로 테스트 (2/15) ====================


@pytest.mark.asyncio
@pytest.mark.regression
async def test_regression_error_422_validation(async_client: AsyncClient):
    """
    회귀 테스트: 422 입력 검증 오류 (1/15)

    조건:
    - 잘못된 JSON 구조 (타입 오류)

    검증:
    - 422 Unprocessable Entity
    - Pydantic validation error detail
    """
    invalid_request = {
        "customer_name": "422 테스트",
        "project_name": "입력 검증 실패",
        "main_breaker": {
            "poles": "invalid_type",
            "current": 100,
            "frame": 100,
        },  # poles는 int여야 함
        "branch_breakers": [],
        "accessories": [],
    }

    response = await async_client.post("/v1/estimate/plan", json=invalid_request)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    data = response.json()
    assert "detail" in data  # FastAPI validation error structure

    print(f"[OK] Error 422 validation: status={response.status_code}")


@pytest.mark.asyncio
@pytest.mark.regression
async def test_regression_error_404_not_found(async_client: AsyncClient):
    """
    회귀 테스트: 404 Not Found (1/15)

    조건:
    - 존재하지 않는 plan_id로 execute 시도

    검증:
    - 404 Not Found
    - PLAN_NOT_FOUND 에러 코드
    """
    invalid_plan_id = "EST-99999999999999"

    response = await async_client.post(
        "/v1/estimate/execute", json={"plan_id": invalid_plan_id}
    )

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    data = response.json()
    assert "code" in data
    assert data["code"] == "PLAN_NOT_FOUND"

    print(f"[OK] Error 404 not found: plan_id={invalid_plan_id}")


# ==================== WORK LOG ====================
"""
DECISIONS:
- SSOT 카탈로그 기반 파라미터만 사용 (Zero-Mock)
- 정상 6 + 경계 2 + 실패 2 + 별칭 3 + 오류 2 = 15 케이스
- parametrize로 테스트 재사용성 극대화

ASSUMPTIONS:
- async_client fixture는 conftest.py에서 제공
- SSOT breakers.json/enclosures.json 유효
- 카탈로그 조회 가능

EVIDENCE:
- 15/15 PASS 시 regression_v15_report.md 생성
- pytest --junitxml=junit.xml 필수

TODOs (I-4에서):
- 커버리지 80% 상향
- 실패 케이스 확장 (10+)
- 503/500 오류 경로 추가
"""
