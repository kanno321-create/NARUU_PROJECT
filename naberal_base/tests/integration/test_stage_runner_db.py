"""
Phase I-6 Restored: stage_runner.py DB integration (simplified)

SB-05 Compliance:
- @requires_db: Real PostgreSQL operations allowed
- No mocks: Actual stage execution
- search_path="kis_beta,public" enforced (SB-01)

Coverage Target: stage_runner.py Stage0→1→2 happy paths
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


@pytest.mark.asyncio
@pytest.mark.requires_db
class TestStageRunnerSimple:
    """Integration tests for StageRunner with real DB"""

    async def test_stage0_pre_validation(self, async_session: AsyncSession):
        """Stage 0: Pre-Validation success path"""
        runner = StageRunner()
        plan = {}
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "실내",
            "main_breaker": {"poles": 2, "ampere": 60, "frame_af": 100},
            "branch_breakers": [{"poles": 2, "ampere": 20, "frame_af": 50}],
        }
        result = await runner.run_stage(0, plan, context)
        assert result is not None
        assert result.get("stage_number") == 0

    async def test_stage1_enclosure(self, async_session: AsyncSession):
        """Stage 1: PickEnclosure with enclosure solver"""
        runner = StageRunner()
        plan = {}
        context = {
            "enclosure_type": "옥내노출",
            "main_breaker": {"poles": 2, "ampere": 60, "frame_af": 100},
            "branch_breakers": [{"poles": 2, "ampere": 20, "frame_af": 50}],
        }
        result = await runner.run_stage(1, plan, context)
        assert result is not None
        assert result.get("stage_number") == 1

    async def test_stage2_layout(self, async_session: AsyncSession):
        """Stage 2: Layout (Breaker Placement)"""
        runner = StageRunner()
        plan = {}
        context = {
            "main_breaker": {"poles": 2, "ampere": 60, "frame_af": 100},
            "branch_breakers": [
                {"poles": 2, "ampere": 20, "frame_af": 50},
                {"poles": 2, "ampere": 30, "frame_af": 50},
            ],
            "enclosure": {"W": 600, "H": 800, "D": 200},
        }
        result = await runner.run_stage(2, plan, context)
        assert result is not None
        assert result.get("stage_number") == 2
