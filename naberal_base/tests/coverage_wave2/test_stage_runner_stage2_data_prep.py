"""
Wave 2 Test - Stage Runner Stage 2 Data Preparation

Coverage Targets:
- stage_runner.py Stage 2 breakers/panel_spec data preparation (Lines 298-356)
- Breakers data auto-generation from main_breaker/branch_breakers
- panel_spec extraction from enclosure (dimensions/model_dump/fallback)

Zero-Mock Principle: Real StageRunner, real EnclosureResult objects
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStage2DataPreparation:
    """Stage 2 breakers/panel_spec 데이터 준비 테스트 (Lines 298-356)"""

    @pytest.mark.asyncio
    async def test_stage2_breakers_data_preparation_from_main_branch(
        self, context_without_breakers_data
    ):
        """breakers 데이터 자동 생성 테스트

        Target: Lines 300-323
        Scenario:
            - Context에 'breakers' 필드 없음
            - main_breaker와 branch_breakers만 존재
            - Stage 2가 자동으로 breakers_data 생성

        Expected:
            - breakers 리스트 생성됨
            - MAIN + BR1, BR2 구조
            - BreakerInput 필드 완비 (id, poles, current_a, width_mm, ...)
        """
        # Arrange: Plan with PLACE verb
        plan = {"steps": [{"PLACE": {}}]}

        # context_without_breakers_data has main_breaker/branch_breakers but NO 'breakers'
        runner = StageRunner()

        # Act: Run Stage 2 (Layout)
        result = await runner.run_stage(2, plan, context_without_breakers_data)

        # Assert: Stage 2 completed
        assert result["status"] in ["success", "error"], "Stage 2 should complete"

        # Assert: 'breakers' field created in context
        assert (
            "breakers" in context_without_breakers_data
        ), "breakers should be auto-generated"

        breakers = context_without_breakers_data["breakers"]
        assert isinstance(breakers, list), "breakers should be a list"
        assert len(breakers) == 3, "Should have 3 breakers: MAIN + 2 branch"

        # Assert: MAIN breaker structure
        main_breaker = breakers[0]
        assert main_breaker["id"] == "MAIN", "First breaker should be MAIN"
        assert main_breaker["poles"] == 3, "MAIN should have 3 poles"
        assert main_breaker["current_a"] == 100, "MAIN should be 100A"
        assert "width_mm" in main_breaker, "width_mm should be present"
        assert "height_mm" in main_breaker, "height_mm should be present"
        assert "depth_mm" in main_breaker, "depth_mm should be present"
        assert "breaker_type" in main_breaker, "breaker_type should be present"

        # Assert: Branch breakers structure
        br1 = breakers[1]
        assert br1["id"] == "BR1", "Second breaker should be BR1"
        assert br1["poles"] == 2, "BR1 should have 2 poles"
        assert br1["current_a"] == 30, "BR1 should be 30A"

        br2 = breakers[2]
        assert br2["id"] == "BR2", "Third breaker should be BR2"
        assert br2["poles"] == 2, "BR2 should have 2 poles"
        assert br2["current_a"] == 20, "BR2 should be 20A"

    @pytest.mark.asyncio
    async def test_stage2_panel_spec_from_dimensions_attribute(
        self, context_with_enclosure_for_stage2
    ):
        """panel_spec extraction from enclosure.dimensions

        Target: Lines 330-337
        Scenario:
            - enclosure has 'dimensions' attribute
            - panel_spec extracted from dimensions

        Expected:
            - panel_spec dict created
            - width_mm, height_mm, depth_mm from dimensions
            - clearance_mm = 50 (default)
        """
        # Arrange
        plan = {"steps": [{"PLACE": {}}]}

        # context_with_enclosure_for_stage2 has enclosure with dimensions attribute
        context = context_with_enclosure_for_stage2.copy()
        # Remove panel_spec to force extraction
        if "panel_spec" in context:
            del context["panel_spec"]

        runner = StageRunner()

        # Act
        result = await runner.run_stage(2, plan, context)

        # Assert: Stage 2 completed
        assert result["status"] in ["success", "error"], "Stage 2 should complete"

        # Assert: panel_spec created from dimensions
        assert "panel_spec" in context, "panel_spec should be auto-generated"

        panel_spec = context["panel_spec"]
        assert isinstance(panel_spec, dict), "panel_spec should be dict"

        # From enclosure_with_model_dump fixture: 700×900×250
        assert (
            panel_spec["width_mm"] == 700
        ), "width_mm should match enclosure dimensions"
        assert (
            panel_spec["height_mm"] == 900
        ), "height_mm should match enclosure dimensions"
        assert (
            panel_spec["depth_mm"] == 250
        ), "depth_mm should match enclosure dimensions"
        assert panel_spec["clearance_mm"] == 50, "clearance_mm should be default 50"

    @pytest.mark.asyncio
    async def test_stage2_panel_spec_from_model_dump(self):
        """panel_spec extraction from enclosure.model_dump() (Pydantic style)

        Target: Lines 338-346
        Scenario:
            - enclosure has model_dump() method
            - panel_spec extracted from dumped dict

        Expected:
            - panel_spec created from model_dump()['dimensions']
        """
        # Arrange
        from kis_estimator_core.models.enclosure import (
            EnclosureResult,
            EnclosureDimensions,
            QualityGateResult,
        )

        dimensions = EnclosureDimensions(width_mm=800, height_mm=1000, depth_mm=300)
        quality_gate = QualityGateResult(
            name="fit_score",
            actual=0.95,
            threshold=0.90,
            passed=True,
            operator=">=",
            critical=True,
        )
        enclosure = EnclosureResult(
            dimensions=dimensions,
            quality_gate=quality_gate,
            candidates=[],
            calculation_details={},
        )

        plan = {"steps": [{"PLACE": {}}]}

        context = {
            "enclosure_type": "옥내노출",
            "install_location": "1층",
            "main_breaker": {"poles": 3, "current": 100},
            "branch_breakers": [{"poles": 2, "current": 30}],
            "enclosure": enclosure,
            "enclosure_result": enclosure,
            # NO 'panel_spec' - will be auto-generated
        }

        runner = StageRunner()

        # Act
        result = await runner.run_stage(2, plan, context)

        # Assert: Stage 2 completed
        assert result["status"] in ["success", "error"], "Stage 2 should complete"

        # Assert: panel_spec created from model_dump()
        assert "panel_spec" in context, "panel_spec should be auto-generated"

        panel_spec = context["panel_spec"]
        assert panel_spec["width_mm"] == 800, "width_mm should match from model_dump"
        assert panel_spec["height_mm"] == 1000, "height_mm should match from model_dump"
        assert panel_spec["depth_mm"] == 300, "depth_mm should match from model_dump"
        assert panel_spec["clearance_mm"] == 50, "clearance_mm should be default 50"

    @pytest.mark.asyncio
    async def test_stage2_panel_spec_fallback_default(
        self, context_with_enclosure_no_dimensions
    ):
        """panel_spec fallback to default values

        Target: Lines 348-355
        Scenario:
            - enclosure exists but has no 'dimensions' attribute
            - enclosure does not have 'model_dump()' method
            - Fallback to default panel_spec

        Expected:
            - panel_spec = 600×800×200mm (default)
        """
        # Arrange
        plan = {"steps": [{"PLACE": {}}]}

        # context_with_enclosure_no_dimensions has enclosure but no dimensions/model_dump
        context = context_with_enclosure_no_dimensions.copy()

        runner = StageRunner()

        # Act
        result = await runner.run_stage(2, plan, context)

        # Assert: Stage 2 completed
        assert result["status"] in ["success", "error"], "Stage 2 should complete"

        # Assert: panel_spec created with fallback defaults
        assert "panel_spec" in context, "panel_spec should be auto-generated"

        panel_spec = context["panel_spec"]
        assert panel_spec["width_mm"] == 600, "Fallback width_mm should be 600"
        assert panel_spec["height_mm"] == 800, "Fallback height_mm should be 800"
        assert panel_spec["depth_mm"] == 200, "Fallback depth_mm should be 200"
        assert panel_spec["clearance_mm"] == 50, "clearance_mm should be 50"

    @pytest.mark.asyncio
    async def test_stage2_breakers_and_panel_spec_both_prepared(self):
        """Complete data preparation flow

        Target: Lines 298-356 (전체 경로)
        Scenario:
            - Context has neither 'breakers' nor 'panel_spec'
            - Stage 2 prepares both automatically
            - PLACE verb executes successfully

        Expected:
            - breakers generated from main_breaker/branch_breakers
            - panel_spec generated from enclosure (or fallback)
            - placements created successfully
        """
        # Arrange
        from kis_estimator_core.models.enclosure import (
            EnclosureResult,
            EnclosureDimensions,
            QualityGateResult,
        )

        dimensions = EnclosureDimensions(width_mm=700, height_mm=900, depth_mm=250)
        quality_gate = QualityGateResult(
            name="fit_score",
            actual=0.92,
            threshold=0.90,
            passed=True,
            operator=">=",
            critical=True,
        )
        enclosure = EnclosureResult(
            dimensions=dimensions,
            quality_gate=quality_gate,
            candidates=[],
            calculation_details={},
        )

        plan = {"steps": [{"PLACE": {}}]}

        context = {
            "enclosure_type": "옥내노출",
            "install_location": "1층",
            "main_breaker": {"poles": 4, "current": 100, "width_mm": 100},
            "branch_breakers": [
                {"poles": 2, "current": 30, "width_mm": 50},
                {"poles": 2, "current": 20, "width_mm": 50},
            ],
            "enclosure": enclosure,
            "enclosure_result": enclosure,
            # NO 'breakers', NO 'panel_spec' - both will be auto-generated
        }

        runner = StageRunner()

        # Act
        result = await runner.run_stage(2, plan, context)

        # Assert: Stage 2 completed
        assert result["status"] in ["success", "error"], "Stage 2 should complete"

        # Assert: breakers auto-generated
        assert "breakers" in context, "breakers should be auto-generated"
        breakers = context["breakers"]
        assert len(breakers) == 3, "Should have 3 breakers (MAIN + 2 branch)"
        assert breakers[0]["id"] == "MAIN", "First should be MAIN"
        assert breakers[1]["id"] == "BR1", "Second should be BR1"
        assert breakers[2]["id"] == "BR2", "Third should be BR2"

        # Assert: panel_spec auto-generated
        assert "panel_spec" in context, "panel_spec should be auto-generated"
        panel_spec = context["panel_spec"]
        assert panel_spec["width_mm"] == 700, "width_mm from enclosure dimensions"
        assert panel_spec["height_mm"] == 900, "height_mm from enclosure dimensions"
        assert panel_spec["depth_mm"] == 250, "depth_mm from enclosure dimensions"

        # Assert: placements created (if Stage 2 succeeded)
        if result["status"] == "success":
            assert "placements" in context, "placements should be created"
            assert len(context["placements"]) > 0, "placements should not be empty"
