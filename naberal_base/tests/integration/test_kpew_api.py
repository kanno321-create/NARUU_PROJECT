"""
K-PEW API Integration Tests

Tests REST API endpoints with real database integration.
Only runs if database credentials are available.
"""

import pytest
from fastapi.testclient import TestClient
import os

# Skip in CI - requires real Supabase with epdl_plans and execution_history tables
pytestmark = [
    pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Skipping K-PEW API tests in CI - requires real Supabase with KPEW tables"
    ),
    pytest.mark.skipif(
        not os.getenv("SUPABASE_DB_URL") and not os.getenv("DATABASE_URL"),
        reason="Database not configured (SUPABASE_DB_URL or DATABASE_URL not set)",
    ),
]


@pytest.fixture
def client():
    """Create FastAPI test client"""
    from api.main import app

    return TestClient(app)


@pytest.fixture
def skip_llm_tests():
    """Skip tests requiring LLM API if ANTHROPIC_API_KEY not set"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set - skipping LLM tests")


def test_kpew_router_registered(client):
    """Test K-PEW router is properly registered"""
    # Get OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    paths = schema.get("paths", {})

    # Check K-PEW endpoints exist
    assert "/v1/estimate/plan" in paths
    assert "/v1/estimate/execute" in paths
    assert "/v1/estimate/{estimate_id}" in paths

    print("\n[SUCCESS] K-PEW router registered with 3 endpoints")


def test_plan_endpoint_validation(client):
    """Test /v1/estimate/plan endpoint input validation"""
    # Missing required fields
    response = client.post("/v1/estimate/plan", json={})
    assert response.status_code == 422  # FastAPI validation error

    # Invalid customer_name (empty)
    response = client.post(
        "/v1/estimate/plan",
        json={
            "customer_name": "",
            "project_name": "테스트",
            "main_breaker": {"poles": 3, "current": 100},
            "branch_breakers": [],
        },
    )
    assert response.status_code == 422

    print("\n[SUCCESS] Plan endpoint validation working")


def test_plan_generation_real_llm(client, skip_llm_tests):
    """Test POST /v1/estimate/plan with REAL Claude API

    WARNING: This test makes a REAL API call to Claude!
    - Costs money (token usage)
    - Requires ANTHROPIC_API_KEY
    - May take 2-5 seconds
    """
    # Prepare request
    request_data = {
        "customer_name": "테스트고객",
        "project_name": "API통합테스트",
        "enclosure_type": "옥내노출",
        "breaker_brand": "상도차단기",
        "main_breaker": {"poles": 3, "current": 100, "frame": 100},
        "branch_breakers": [
            {"poles": 2, "current": 20, "frame": 50},
            {"poles": 2, "current": 30, "frame": 50},
        ],
        "accessories": [],
    }

    # Make REAL API call
    response = client.post("/v1/estimate/plan", json=request_data)

    # Verify response
    assert (
        response.status_code == 201
    ), f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()

    # Validate response structure
    assert "plan_id" in data
    assert data["plan_id"].startswith("EST-")
    assert "epdl_json" in data
    assert "llm_model" in data
    assert "token_usage" in data
    assert data["is_valid"] is True

    # Validate EPDL structure
    epdl = data["epdl_json"]
    assert "version" in epdl
    assert "steps" in epdl
    assert isinstance(epdl["steps"], list)

    print(f"\n[SUCCESS] Plan created: {data['plan_id']}")
    print(f"  Model: {data['llm_model']}")
    print(f"  Tokens: {data['token_usage']['total']}")
    print(f"  Steps: {len(epdl['steps'])}")

    # Return plan_id for further tests
    return data["plan_id"]


def test_execute_endpoint_not_found(client):
    """Test /v1/estimate/execute with non-existent plan_id"""
    response = client.post(
        "/v1/estimate/execute", json={"plan_id": "EST-99999999999999"}
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"]["code"] == "PLAN_NOT_FOUND"

    print("\n[SUCCESS] Execute endpoint returns 404 for non-existent plan")


def test_get_estimate_not_found(client):
    """Test GET /v1/estimate/{estimate_id} - Not Implemented endpoint"""
    response = client.get("/v1/estimate/EST-99999999999999")

    # GET 엔드포인트가 아직 구현되지 않음 (501 Not Implemented)
    assert response.status_code == 501
    data = response.json()
    assert "detail" in data
    assert "message" in data["detail"]
    assert "구현 예정" in data["detail"]["message"]

    print("\n[SUCCESS] Get estimate returns 501 Not Implemented")


def test_full_workflow_real_database(client, skip_llm_tests):
    """
    Test full K-PEW workflow with REAL database integration

    Flow:
    1. Generate plan (Claude API)
    2. Verify plan saved to database
    3. Execute plan (8-stage pipeline)
    4. Retrieve estimate details

    WARNING: This is a REAL end-to-end test!
    - Makes REAL Claude API call
    - Writes to REAL Supabase database
    - Executes REAL 8-stage pipeline
    """
    # Step 1: Generate plan
    plan_request = {
        "customer_name": "통합테스트고객",
        "project_name": "E2E테스트",
        "main_breaker": {"poles": 3, "current": 100, "frame": 100},
        "branch_breakers": [{"poles": 2, "current": 20, "frame": 50}],
    }

    plan_response = client.post("/v1/estimate/plan", json=plan_request)
    assert plan_response.status_code == 201

    plan_data = plan_response.json()
    plan_id = plan_data["plan_id"]

    print(f"\n[STEP 1] Plan created: {plan_id}")

    # Step 2: Retrieve plan (verify database save)
    get_response = client.get(f"/v1/estimate/{plan_id}")
    assert get_response.status_code == 200

    estimate_data = get_response.json()
    assert estimate_data["estimate_id"] == plan_id
    assert "plan" in estimate_data

    print("[STEP 2] Plan retrieved from database")

    # Step 3: Execute plan
    exec_request = {
        "plan_id": plan_id,
        "context": {"enclosure_type": "옥내노출", "breaker_brand": "상도차단기"},
    }

    exec_response = client.post("/v1/estimate/execute", json=exec_request)
    assert exec_response.status_code == 200

    exec_data = exec_response.json()
    assert exec_data["estimate_id"] == plan_id
    assert exec_data["status"] in ["success", "blocked", "error"]
    assert exec_data["total_stages"] == 8

    print(f"[STEP 3] Execution completed: status={exec_data['status']}")
    print(f"  Stages completed: {exec_data['stages_completed']}/8")
    print(f"  Duration: {exec_data['total_duration_ms']}ms")

    # Step 4: Retrieve execution history
    final_response = client.get(f"/v1/estimate/{plan_id}")
    assert final_response.status_code == 200

    final_data = final_response.json()
    assert len(final_data["execution_history"]) > 0

    print(
        f"[STEP 4] Execution history retrieved: {len(final_data['execution_history'])} stages"
    )

    print("\n[SUCCESS] Full workflow test passed!")


# ============================================================================
# API Structure Tests (No LLM Required)
# ============================================================================


def test_api_endpoints_exist():
    """Test K-PEW API endpoints are registered"""
    from api.main import app

    routes = [route.path for route in app.routes]

    assert "/v1/estimate/plan" in routes
    assert "/v1/estimate/execute" in routes
    assert "/v1/estimate/{estimate_id}" in routes

    print("\n[SUCCESS] All 3 K-PEW endpoints registered")


def test_api_router_tags():
    """Test K-PEW router has correct tags"""
    from api.routers.kpew import router

    assert router.prefix == "/v1/estimate"
    assert "kpew" in router.tags

    print("\n[SUCCESS] K-PEW router configuration valid")


def test_response_models_defined():
    """Test all response models are properly defined"""
    from api.routers.kpew import (
        PlanRequest,
        PlanResponse,
        ExecuteRequest,
        ExecuteResponse,
        EstimateDetailResponse,
    )

    # Verify models can be instantiated
    assert PlanRequest
    assert PlanResponse
    assert ExecuteRequest
    assert ExecuteResponse
    assert EstimateDetailResponse

    print("\n[SUCCESS] All response models defined")


# ============================================================================
# Database Integration Tests (No LLM Required)
# ============================================================================


@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection is working"""
    from api.db import get_db
    from sqlalchemy import text

    async for session in get_db():
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        print("\n[SUCCESS] Database connection verified")
        break


@pytest.mark.asyncio
async def test_epdl_plans_table_exists():
    """Test epdl_plans table exists in database"""
    from api.db import get_db
    from sqlalchemy import text

    async for session in get_db():
        # Check table exists
        result = await session.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'epdl_plans'
                )
            """
            )
        )
        table_exists = result.scalar()
        assert table_exists, "epdl_plans table does not exist"

        print("\n[SUCCESS] epdl_plans table exists")
        break


@pytest.mark.asyncio
async def test_execution_history_table_exists():
    """Test execution_history table exists in database"""
    from api.db import get_db
    from sqlalchemy import text

    async for session in get_db():
        result = await session.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'execution_history'
                )
            """
            )
        )
        table_exists = result.scalar()
        assert table_exists, "execution_history table does not exist"

        print("\n[SUCCESS] execution_history table exists")
        break
