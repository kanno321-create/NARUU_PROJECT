"""
I-3.4 Plan→Execute Flow Integration Tests

Tests VerbSpec-based plan/execute workflow with real database integration.
No LLM required (deterministic VerbSpec generation).

Test Coverage:
1. POST /v1/estimate/plan → 201 (VerbSpec generation + DB save)
2. POST /v1/estimate/execute → 200 (VerbSpec execution)
3. POST /v1/estimate/execute → 404 (plan not found)
4. Deprecated alias: POST /v1/estimate → POST /v1/estimate/plan
"""

import pytest
import os


# Only run if database is configured
pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL") and not os.getenv("DATABASE_URL"),
    reason="Database not configured (SUPABASE_DB_URL or DATABASE_URL not set)",
)


# AsyncClient fixture is provided by conftest.py (async_client)


@pytest.fixture
def sample_plan_request():
    """Sample PlanRequest for testing"""
    return {
        "customer_name": "I-3.4 테스트고객",
        "project_name": "VerbSpec 통합테스트",
        "enclosure_type": "옥내노출",
        "breaker_brand": "상도차단기",
        "main_breaker": {"poles": 3, "current": 100, "frame": 100},
        "branch_breakers": [
            {"poles": 2, "current": 20, "frame": 50},
            {"poles": 2, "current": 30, "frame": 50},
            {"poles": 3, "current": 50, "frame": 100},
        ],
        "accessories": [],
    }


# ============================================================================
# Test 1: POST /v1/estimate/plan - VerbSpec Generation & DB Save
# ============================================================================


@pytest.mark.asyncio
async def test_plan_generation_verbspec(async_client, sample_plan_request):
    """
    Test POST /v1/estimate/plan with VerbSpec generation (I-3.4)

    Expected:
    - 201 Created
    - Response contains plan_id, verb_specs, specs_count
    - VerbSpec list contains PICK_ENCLOSURE + PLACE
    - VerbSpecs pass Pydantic validation
    - Saved to verb_plans table

    NO LLM REQUIRED - deterministic generation
    """
    # Make API call
    response = await async_client.post("/v1/estimate/plan", json=sample_plan_request)

    # Verify response status
    assert (
        response.status_code == 201
    ), f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()

    # Verify response structure (I-3.4 schema)
    assert "plan_id" in data, "Missing plan_id"
    assert "estimate_id" in data, "Missing estimate_id"
    assert "verb_specs" in data, "Missing verb_specs"
    assert "specs_count" in data, "Missing specs_count"
    assert "is_valid" in data, "Missing is_valid"
    assert "created_at" in data, "Missing created_at"

    # Verify plan_id format
    assert data["plan_id"].startswith(
        "EST-"
    ), f"Invalid plan_id format: {data['plan_id']}"
    assert data["estimate_id"] == data["plan_id"], "estimate_id should equal plan_id"

    # Verify VerbSpec structure
    verb_specs = data["verb_specs"]
    assert isinstance(verb_specs, list), "verb_specs should be a list"
    assert (
        len(verb_specs) == 2
    ), f"Expected 2 VerbSpecs (PICK_ENCLOSURE + PLACE), got {len(verb_specs)}"
    assert (
        data["specs_count"] == 2
    ), f"specs_count should be 2, got {data['specs_count']}"

    # Verify PICK_ENCLOSURE VerbSpec
    pick_spec = verb_specs[0]
    assert (
        pick_spec["verb_name"] == "PICK_ENCLOSURE"
    ), f"First VerbSpec should be PICK_ENCLOSURE, got {pick_spec['verb_name']}"
    assert "params" in pick_spec, "PICK_ENCLOSURE missing params"
    assert "version" in pick_spec, "PICK_ENCLOSURE missing version"
    assert (
        pick_spec["params"]["enclosure_type"] == "옥내노출"
    ), "enclosure_type mismatch"
    assert (
        pick_spec["params"]["material"] == "STEEL"
    ), "material should default to STEEL"
    assert (
        pick_spec["params"]["thickness"] == "1.6T"
    ), "thickness should default to 1.6T"

    # Verify PLACE VerbSpec
    place_spec = verb_specs[1]
    assert (
        place_spec["verb_name"] == "PLACE"
    ), f"Second VerbSpec should be PLACE, got {place_spec['verb_name']}"
    assert "params" in place_spec, "PLACE missing params"
    assert "breakers" in place_spec["params"], "PLACE missing breakers param"
    breaker_ids = place_spec["params"]["breakers"]
    assert breaker_ids[0] == "MAIN", "First breaker should be MAIN"
    assert (
        len(breaker_ids) == 4
    ), f"Expected 4 breakers (MAIN + 3 branches), got {len(breaker_ids)}"

    # Verify validation status
    assert data["is_valid"] is True, "VerbSpecs should pass validation"

    print(f"\n[SUCCESS] Plan created: {data['plan_id']}")
    print(f"  VerbSpecs: {data['specs_count']}")
    print(f"  PICK_ENCLOSURE params: {len(pick_spec['params'])} fields")
    print(f"  PLACE breakers: {len(breaker_ids)} breakers")

    return data["plan_id"]


# ============================================================================
# Test 2: POST /v1/estimate/execute - VerbSpec Execution
# ============================================================================


@pytest.mark.asyncio
async def test_execute_verbspec_plan(async_client, sample_plan_request):
    """
    Test POST /v1/estimate/execute with VerbSpec plan (I-3.4)

    Flow:
    1. Create plan via /v1/estimate/plan
    2. Execute plan via /v1/estimate/execute
    3. Verify execution results

    Expected:
    - 200 OK
    - Execution completes (success/blocked/error)
    - execution_history saved to DB
    """
    # Step 1: Create plan
    plan_response = await async_client.post(
        "/v1/estimate/plan", json=sample_plan_request
    )
    assert (
        plan_response.status_code == 201
    ), f"Plan creation failed: {plan_response.text}"

    plan_data = plan_response.json()
    plan_id = plan_data["plan_id"]

    print(f"\n[STEP 1] Plan created: {plan_id}")

    # Step 2: Execute plan
    exec_request = {
        "plan_id": plan_id,
        "context": {"enclosure_type": "옥내노출", "breaker_brand": "상도차단기"},
    }

    exec_response = await async_client.post("/v1/estimate/execute", json=exec_request)
    assert (
        exec_response.status_code == 200
    ), f"Expected 200, got {exec_response.status_code}: {exec_response.text}"

    exec_data = exec_response.json()

    # Verify response structure
    assert "estimate_id" in exec_data, "Missing estimate_id"
    assert "status" in exec_data, "Missing status"
    assert "stages_completed" in exec_data, "Missing stages_completed"
    assert "total_stages" in exec_data, "Missing total_stages"
    assert "total_duration_ms" in exec_data, "Missing total_duration_ms"
    assert "quality_gates" in exec_data, "Missing quality_gates"

    # Verify estimate_id matches
    assert (
        exec_data["estimate_id"] == plan_id
    ), f"estimate_id mismatch: {exec_data['estimate_id']} != {plan_id}"

    # Verify execution status
    assert exec_data["status"] in [
        "success",
        "blocked",
        "error",
    ], f"Invalid status: {exec_data['status']}"

    # Verify total_stages
    assert (
        exec_data["total_stages"] == 8
    ), f"Expected 8 stages, got {exec_data['total_stages']}"

    # Verify quality_gates structure
    quality_gates = exec_data["quality_gates"]
    assert "all_passed" in quality_gates, "quality_gates missing all_passed"
    assert "stages" in quality_gates, "quality_gates missing stages"

    print("[STEP 2] Execution completed")
    print(f"  Status: {exec_data['status']}")
    print(
        f"  Stages completed: {exec_data['stages_completed']}/{exec_data['total_stages']}"
    )
    print(f"  Duration: {exec_data['total_duration_ms']}ms")
    print(f"  Quality gates passed: {quality_gates['all_passed']}")

    print("\n[SUCCESS] Plan→Execute flow completed")


# ============================================================================
# Test 3: POST /v1/estimate/execute - 404 Not Found
# ============================================================================


@pytest.mark.asyncio
async def test_execute_plan_not_found(async_client):
    """
    Test POST /v1/estimate/execute with non-existent plan_id (I-3.4)

    Expected:
    - 404 Not Found
    - Error code: PLAN_NOT_FOUND
    - Hint message present
    """
    # Execute with non-existent plan_id
    exec_request = {"plan_id": "EST-99999999999999"}

    response = await async_client.post("/v1/estimate/execute", json=exec_request)

    # Verify 404 status
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    data = response.json()

    # Verify error structure (I-3.4: error_handler unwraps detail dict)
    assert "code" in data, "Missing error code"
    assert (
        data["code"] == "PLAN_NOT_FOUND"
    ), f"Expected PLAN_NOT_FOUND, got {data['code']}"

    assert "message" in data, "Missing error message"
    assert (
        "EST-99999999999999" in data["message"]
    ), "Error message should contain plan_id"

    assert "hint" in data, "Missing hint"
    assert (
        "POST /v1/estimate/plan" in data["hint"]
    ), "Hint should mention plan creation endpoint"

    print("\n[SUCCESS] Execute with non-existent plan returns 404")
    print(f"  Error code: {data['code']}")
    print(f"  Message: {data['message']}")


# ============================================================================
# Test 4: Deprecated Alias - POST /v1/estimate → /v1/estimate/plan
# ============================================================================


@pytest.mark.asyncio
async def test_deprecated_alias_estimate_to_plan(async_client, sample_plan_request):
    """
    Test deprecated alias: POST /v1/estimate → POST /v1/estimate/plan (I-3.4)

    Expected:
    - Both endpoints return identical results
    - Same plan_id format
    - Same VerbSpec structure

    This ensures backward compatibility for existing clients.
    """
    # Call /v1/estimate/plan (new endpoint)
    plan_response = await async_client.post(
        "/v1/estimate/plan", json=sample_plan_request
    )
    assert plan_response.status_code == 201
    plan_data = plan_response.json()

    # Call /v1/estimate (deprecated alias)
    alias_response = await async_client.post("/v1/estimate", json=sample_plan_request)
    assert alias_response.status_code == 201
    alias_data = alias_response.json()

    # Verify both responses have same structure
    assert set(plan_data.keys()) == set(
        alias_data.keys()
    ), "Response structure mismatch"

    # Verify both responses have same VerbSpec count
    assert plan_data["specs_count"] == alias_data["specs_count"], "specs_count mismatch"
    assert len(plan_data["verb_specs"]) == len(
        alias_data["verb_specs"]
    ), "verb_specs length mismatch"

    # Verify VerbSpec verb_name order is same
    plan_verbs = [spec["verb_name"] for spec in plan_data["verb_specs"]]
    alias_verbs = [spec["verb_name"] for spec in alias_data["verb_specs"]]
    assert (
        plan_verbs == alias_verbs
    ), f"VerbSpec order mismatch: {plan_verbs} != {alias_verbs}"

    print(
        "\n[SUCCESS] Deprecated alias /v1/estimate works identically to /v1/estimate/plan"
    )
    print(f"  /v1/estimate/plan → plan_id: {plan_data['plan_id']}")
    print(f"  /v1/estimate      → plan_id: {alias_data['plan_id']}")
    print(f"  Both return {plan_data['specs_count']} VerbSpecs")


# ============================================================================
# Database Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_verb_plans_table_exists():
    """
    Test verb_plans table exists in database (I-3.4)

    Verifies:
    - verb_plans table exists
    - Required columns present (plan_id, specs_json, specs_count, is_valid, created_at, updated_at)
    """
    from api.db import get_db
    from sqlalchemy import text

    async for session in get_db():
        # Check table exists
        result = await session.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'verb_plans'
                )
            """
            )
        )
        table_exists = result.scalar()
        assert (
            table_exists
        ), "verb_plans table does not exist - run migration: db/migrations/20251015_verb_plans.sql"

        # Check columns exist
        result = await session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'verb_plans'
            """
            )
        )
        columns = [row[0] for row in result.fetchall()]

        required_columns = [
            "plan_id",
            "specs_json",
            "specs_count",
            "is_valid",
            "created_at",
            "updated_at",
        ]
        for col in required_columns:
            assert col in columns, f"Missing required column: {col}"

        print("\n[SUCCESS] verb_plans table exists with all required columns")
        print(f"  Columns: {', '.join(columns)}")
        break


@pytest.mark.asyncio
async def test_plan_saved_to_database(async_client, sample_plan_request):
    """
    Test plan is actually saved to verb_plans table (I-3.4)

    Verifies Zero-Mock compliance:
    - Plan saved to REAL database
    - specs_json is valid JSON
    - specs_count matches actual count
    """
    from api.db import get_db
    from sqlalchemy import text
    import json

    # Create plan
    response = await async_client.post("/v1/estimate/plan", json=sample_plan_request)
    assert response.status_code == 201

    plan_data = response.json()
    plan_id = plan_data["plan_id"]

    # Query database directly
    async for session in get_db():
        result = await session.execute(
            text(
                "SELECT plan_id, specs_json, specs_count, is_valid FROM verb_plans WHERE plan_id = :plan_id"
            ),
            {"plan_id": plan_id},
        )
        row = result.fetchone()

        assert row is not None, f"Plan {plan_id} not found in database"

        db_plan_id, db_specs_json, db_specs_count, db_is_valid = row

        # Verify plan_id
        assert db_plan_id == plan_id, f"plan_id mismatch: {db_plan_id} != {plan_id}"

        # Verify specs_json is valid JSON (I-3.4: asyncpg auto-parses JSONB to Python objects)
        if isinstance(db_specs_json, str):
            specs = json.loads(db_specs_json)
        else:
            specs = db_specs_json  # Already parsed by asyncpg

        assert isinstance(specs, list), "specs_json should be a list"
        assert len(specs) == 2, f"Expected 2 VerbSpecs, got {len(specs)}"

        # Verify specs_count
        assert db_specs_count == len(
            specs
        ), f"specs_count mismatch: {db_specs_count} != {len(specs)}"

        # Verify is_valid
        assert db_is_valid is True, "is_valid should be True"

        print(f"\n[SUCCESS] Plan {plan_id} saved to database")
        print(f"  specs_count: {db_specs_count}")
        print(f"  is_valid: {db_is_valid}")
        print(f"  VerbSpecs: {[s['verb_name'] for s in specs]}")

        break
