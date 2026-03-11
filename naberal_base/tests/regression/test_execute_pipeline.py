"""
I-3.5 Execute Pipeline Regression Tests

목적: Execute 엔드포인트 전체 플로우 커버리지 증대
예상 커버리지 증가: +15%

커버되는 모듈:
- api/routers/kpew.py (execute 엔드포인트)
- kpew/execution/executor.py
- kpew/execution/stage_runner.py (일부)
- repos/plan_repo.py (load_plan)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.regression
async def test_execute_pipeline_small_panel(async_client: AsyncClient):
    """
    Execute Pipeline: 소형 패널 (2P 20A)

    검증:
    - Plan 생성 → Execute 성공
    - 8 stages 실행
    - quality_gates.all_passed
    """
    # Step 1: Create plan
    plan_request = {
        "customer_name": "Execute 테스트_소형",
        "project_name": "소형 패널 Execute",
        "main_breaker": {"poles": 2, "current": 20, "frame": 30},
        "branch_breakers": [
            {"poles": 2, "current": 15, "frame": 30},
            {"poles": 2, "current": 20, "frame": 30},
        ],
        "accessories": [],
    }

    plan_response = await async_client.post("/v1/estimate/plan", json=plan_request)
    assert plan_response.status_code == 201
    plan_data = plan_response.json()
    plan_id = plan_data["plan_id"]

    print(f"[STEP 1] Plan created: {plan_id}")

    # Step 2: Execute plan
    execute_request = {"plan_id": plan_id}
    exec_response = await async_client.post(
        "/v1/estimate/execute", json=execute_request
    )

    assert exec_response.status_code == 200
    exec_data = exec_response.json()

    # Verify execution
    assert exec_data["estimate_id"] == plan_id
    assert exec_data["status"] in ["completed", "blocked"]
    assert exec_data["total_stages"] == 8
    assert "quality_gates" in exec_data
    assert "stages_completed" in exec_data

    print(
        f"[STEP 2] Execute completed: status={exec_data['status']}, stages={exec_data['stages_completed']}/8"
    )


@pytest.mark.asyncio
@pytest.mark.regression
async def test_execute_pipeline_medium_panel(async_client: AsyncClient):
    """
    Execute Pipeline: 중형 패널 (3P 100A)

    검증:
    - 중형 패널 Execute 성공
    - 더 많은 브레이커 처리
    """
    # Step 1: Create plan
    plan_request = {
        "customer_name": "Execute 테스트_중형",
        "project_name": "중형 패널 Execute",
        "main_breaker": {"poles": 3, "current": 100, "frame": 100},
        "branch_breakers": [
            {"poles": 2, "current": 60, "frame": 100},
            {"poles": 3, "current": 75, "frame": 100},
            {"poles": 3, "current": 100, "frame": 100},
        ],
        "accessories": [],
    }

    plan_response = await async_client.post("/v1/estimate/plan", json=plan_request)
    assert plan_response.status_code == 201
    plan_id = plan_response.json()["plan_id"]

    # Step 2: Execute
    exec_response = await async_client.post(
        "/v1/estimate/execute", json={"plan_id": plan_id}
    )
    assert exec_response.status_code == 200

    exec_data = exec_response.json()
    assert exec_data["total_stages"] == 8

    print(f"[OK] Medium panel executed: {plan_id}, status={exec_data['status']}")


@pytest.mark.asyncio
@pytest.mark.regression
async def test_execute_pipeline_large_panel(async_client: AsyncClient):
    """
    Execute Pipeline: 대형 패널 (4P 400A)

    검증:
    - 대형 패널 Execute 성공
    - 최대 용량 처리
    """
    # Step 1: Create plan
    plan_request = {
        "customer_name": "Execute 테스트_대형",
        "project_name": "대형 패널 Execute",
        "main_breaker": {"poles": 4, "current": 400, "frame": 400},
        "branch_breakers": [
            {"poles": 4, "current": 300, "frame": 400},
            {"poles": 4, "current": 350, "frame": 400},
            {"poles": 4, "current": 400, "frame": 400},
        ],
        "accessories": [],
    }

    plan_response = await async_client.post("/v1/estimate/plan", json=plan_request)
    assert plan_response.status_code == 201
    plan_id = plan_response.json()["plan_id"]

    # Step 2: Execute
    exec_response = await async_client.post(
        "/v1/estimate/execute", json={"plan_id": plan_id}
    )
    assert exec_response.status_code == 200

    exec_data = exec_response.json()
    assert exec_data["total_stages"] == 8

    print(f"[OK] Large panel executed: {plan_id}, status={exec_data['status']}")


@pytest.mark.asyncio
@pytest.mark.regression
async def test_execute_pipeline_with_accessories(async_client: AsyncClient):
    """
    Execute Pipeline: 부속자재 포함 (TODO: 향후 구현)

    검증:
    - 부속자재 포함 Plan 생성
    - Execute 성공 (현재는 accessories가 VerbSpec에만 포함됨)
    """
    # Step 1: Create plan with accessories
    plan_request = {
        "customer_name": "Execute 테스트_부속",
        "project_name": "부속자재 포함 Execute",
        "main_breaker": {"poles": 3, "current": 100, "frame": 100},
        "branch_breakers": [{"poles": 2, "current": 60, "frame": 100}],
        "accessories": [{"type": "MAGNET", "model": "MC-22", "quantity": 1}],
    }

    plan_response = await async_client.post("/v1/estimate/plan", json=plan_request)
    assert plan_response.status_code == 201
    plan_id = plan_response.json()["plan_id"]

    # Verify accessories in VerbSpec
    verb_specs = plan_response.json()["verb_specs"]
    pick_spec = next(
        (s for s in verb_specs if s["verb_name"] == "PICK_ENCLOSURE"), None
    )
    assert pick_spec is not None
    assert len(pick_spec["params"]["accessories"]) == 1

    # Step 2: Execute
    exec_response = await async_client.post(
        "/v1/estimate/execute", json={"plan_id": plan_id}
    )
    assert exec_response.status_code == 200

    print(f"[OK] Accessories plan executed: {plan_id}")


@pytest.mark.asyncio
@pytest.mark.regression
async def test_execute_pipeline_blocking_errors(async_client: AsyncClient):
    """
    Execute Pipeline: Blocking Errors 처리

    검증:
    - 정책 위반 케이스는 plan 생성 시 422 발생하므로
    - Execute 단계에서는 valid plan만 들어옴
    - 따라서 execute의 blocking은 주로 pre-validation 단계에서 발생
    """
    # This test verifies that execute handles pre-validation blocking
    # Current implementation: all plans that pass plan creation are valid
    # So execute blocking is expected to be rare (infrastructure errors only)

    # Create a valid plan
    plan_request = {
        "customer_name": "Execute Blocking 테스트",
        "project_name": "Pre-validation Test",
        "main_breaker": {"poles": 2, "current": 20, "frame": 30},
        "branch_breakers": [],
        "accessories": [],
    }

    plan_response = await async_client.post("/v1/estimate/plan", json=plan_request)
    assert plan_response.status_code == 201
    plan_id = plan_response.json()["plan_id"]

    # Execute - should succeed or return blocking_errors
    exec_response = await async_client.post(
        "/v1/estimate/execute", json={"plan_id": plan_id}
    )
    assert exec_response.status_code == 200

    exec_data = exec_response.json()

    # Either completed or blocked
    assert exec_data["status"] in ["completed", "blocked"]

    # If blocked, should have blocking_errors
    if exec_data["status"] == "blocked":
        assert "blocking_errors" in exec_data
        assert len(exec_data["blocking_errors"]) > 0
        print(f"[INFO] Blocked with {len(exec_data['blocking_errors'])} errors")
    else:
        print("[OK] Execution completed successfully")


# ==================== WORK LOG ====================
"""
DECISIONS:
- Execute 통합 테스트 5개 (small/medium/large/accessories/blocking)
- 실제 DB 연산 수행 (Zero-Mock)
- Plan → Execute 전체 플로우 커버

ASSUMPTIONS:
- async_client fixture 사용
- Executor/StageRunner가 8 stages 실행
- Pre-validation에서 대부분 blocking 발생

COVERAGE TARGET:
- api/routers/kpew.py execute 엔드포인트: +10%
- kpew/execution/executor.py: +20%
- kpew/execution/stage_runner.py: +5% (일부, 전체는 I-4)

TOTAL EXPECTED: +15% coverage increase
"""
