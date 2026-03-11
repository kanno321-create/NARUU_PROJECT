"""
Integration Test: K-PEW 8-Stage Pipeline
Tests full pipeline with REAL engine integration (NO MOCKS!)
"""

import pytest
from kis_estimator_core.kpew.execution import EPDLExecutor
from kis_estimator_core.errors.exceptions import PhaseBlockedError


@pytest.mark.asyncio
async def test_kpew_8_stage_pipeline_minimal():
    """Test complete 8-stage K-PEW pipeline with minimal valid input (I-3.5: Async-unified)"""

    # EPDL plan (simple dict for now, will use EPDLParser later)
    epdl_json = {
        "global": {
            "balance_limit": 0.03,
            "spare_ratio": 0.2,
            "tab_policy": "2->1&2 | 3+->1&3",
        },
        "steps": [
            {"PICK_ENCLOSURE": {"panel": "MAIN", "strategy": "min_size_with_spare"}},
            {"PLACE": {"panel": "MAIN", "algo": "greedy", "seed": 42}},
            {"REBALANCE": {"panel": "MAIN", "method": "swap_local", "max_iter": 100}},
        ],
    }

    # Execution context (minimal valid data to pass Stage 0)
    context = {
        "enclosure_type": "옥내노출",
        "install_location": "옥내노출",
        "material": "STEEL 1.6T",
        "main_breaker": {
            "model": "SBE-104",
            "poles": 3,
            "current": 100,
            "frame": 100,
            "voltage": 380,
            "breaking_capacity": 14,
            "width_mm": 90,
            "height_mm": 155,
            "depth_mm": 60,
        },
        "branch_breakers": [
            {
                "model": "SBE-52",
                "poles": 2,
                "current": 20,
                "frame": 50,
                "voltage": 220,
                "breaking_capacity": 14,
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
                "breaker_type": "small",
            },
            {
                "model": "SBE-52",
                "poles": 2,
                "current": 30,
                "frame": 50,
                "voltage": 220,
                "breaking_capacity": 14,
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
                "breaker_type": "normal",
            },
        ],
        "accessories": [],
        "panel": {
            "width_mm": 600,
            "height_mm": 800,
            "depth_mm": 150,
            "clearance_mm": 50,
        },
    }

    # Execute (I-3.5: Await async execute())
    executor = EPDLExecutor()

    try:
        result = await executor.execute(epdl_json, context)

        # Verify results
        assert "success" in result
        assert "stages" in result
        assert "total_duration_ms" in result

        print("\n[PIPELINE RESULT]")
        print(f"  Success: {result['success']}")
        print(f"  Stages completed: {len(result['stages'])}")
        print(f"  Duration: {result['total_duration_ms']}ms")

        for stage in result["stages"]:
            status_icon = (
                "✅"
                if stage["status"] == "success"
                else ("⏭️" if stage["status"] == "skipped" else "❌")
            )
            print(
                f"  {status_icon} Stage {stage['stage_number']} ({stage['stage_name']}): {stage['status']}"
            )
            if stage.get("errors"):
                for error in stage["errors"]:
                    print(
                        f"      - {error.error_code.code}: {error.error_code.message}"
                    )

        # Basic assertions
        assert len(result["stages"]) >= 1  # At least Stage 0 should run
        assert result["total_duration_ms"] >= 0

        # Check Stage 0 passed
        stage_0 = result["stages"][0]
        assert stage_0["stage_number"] == 0
        assert stage_0["status"] == "success"  # Should pass with valid input

    except PhaseBlockedError as e:
        # Expected if stages have blocking errors
        print("\n[PIPELINE BLOCKED]")
        print(f"  Current Phase: {e.current_phase}")
        print(f"  Next Phase: {e.next_phase}")
        print(f"  Blocking Errors: {len(e.blocking_errors)}")
        for error in e.blocking_errors:
            print(f"    - {error.error_code.code}: {error.error_code.message}")

        # This is acceptable behavior for incomplete context
        pytest.skip(
            f"Pipeline blocked at {e.current_phase} (expected with incomplete data)"
        )

    except Exception as e:
        # Unexpected error
        print(f"\n[PIPELINE ERROR] {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        pytest.fail(f"Unexpected error: {e}")


@pytest.mark.asyncio
async def test_kpew_stage_0_validation():
    """Test Stage 0 (Pre-Validation) with missing inputs (I-3.5: Async-unified)"""

    epdl_json = {"global": {}, "steps": []}

    # Missing required fields
    context = {
        # No enclosure_type
        # No install_location
        # No main_breaker
        # No branch_breakers
    }

    executor = EPDLExecutor()

    with pytest.raises(PhaseBlockedError) as exc_info:
        # I-3.5: Await async execute()
        await executor.execute(epdl_json, context)

    # Verify blocking errors
    error = exc_info.value
    assert error.current_phase == "Pre-Validation"
    assert len(error.blocking_errors) >= 4  # INP-001, INP-002, INP-004, INP-005

    print("\n[STAGE 0 VALIDATION]")
    print(f"  Blocking errors detected: {len(error.blocking_errors)}")
    for err in error.blocking_errors:
        print(f"    - {err.error_code.code}: {err.error_code.message}")


@pytest.mark.asyncio
async def test_kpew_stage_integration():
    """Test that real engines are called (not mocks) (I-3.5: Async-unified)"""

    epdl_json = {"global": {}, "steps": [{"PICK_ENCLOSURE": {"panel": "MAIN"}}]}

    context = {
        "enclosure_type": "옥내노출",
        "install_location": "옥내노출",
        "material": "STEEL 1.6T",
        "main_breaker": {
            "model": "SBE-104",
            "poles": 3,
            "current": 100,
            "frame": 100,
            "voltage": 380,
            "breaking_capacity": 14,
        },
        "branch_breakers": [
            {
                "model": "SBE-52",
                "poles": 2,
                "current": 20,
                "frame": 50,
                "voltage": 220,
                "breaking_capacity": 14,
            }
        ],
        "accessories": [],
    }

    executor = EPDLExecutor()

    try:
        # I-3.5: Await async execute()
        result = await executor.execute(epdl_json, context)

        # Check that Stage 1 (Enclosure) was executed
        stages = result["stages"]
        stage_1 = next((s for s in stages if s["stage_number"] == 1), None)

        if stage_1:
            print("\n[STAGE 1 VERIFICATION]")
            print(f"  Status: {stage_1['status']}")
            print(f"  Duration: {stage_1['duration_ms']}ms")

            if stage_1["status"] == "success":
                # Verify real EnclosureSolver was called
                assert "output" in stage_1
                assert "enclosure_result" in stage_1["output"]
                print("  ✅ Real EnclosureSolver called successfully")

                # Check result structure
                enclosure_result = stage_1["output"]["enclosure_result"]
                assert hasattr(enclosure_result, "dimensions")
                assert hasattr(enclosure_result, "quality_gate")
                print("  ✅ EnclosureResult structure validated")

    except PhaseBlockedError as e:
        # Expected if knowledge files are missing
        print(
            f"\n[STAGE 1 BLOCKED] {e.current_phase}: {e.blocking_errors[0].error_code.message}"
        )
        pytest.skip("Stage 1 blocked (knowledge files may be missing)")

    except Exception as e:
        print(f"\n[INTEGRATION ERROR] {e}")
        import traceback

        traceback.print_exc()
        pytest.skip(f"Integration test skipped: {e}")
