"""
breaker_critic.py 유닛 테스트 (Stage 2.1)

API 변경사항 (2025-10-05):
- 전류 기반 % → 개수 기반 diff_max
- phase_imbalance_pct → diff_max (0=완벽, 1=허용, >1=위반)
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
from kis_estimator_core.engine.breaker_critic import (  # noqa: E402
    BreakerCritic,
    MAX_LIMITS,
)
from kis_estimator_core.engine.breaker_placer import PlacementResult  # noqa: E402


class TestBreakerCritic:
    """Breaker Critic 유닛 테스트 (개수 기반)"""

    def setup_method(self):
        """각 테스트 전 실행"""
        self.critic = BreakerCritic()

    def test_init(self):
        """TC-001: Critic 초기화"""
        assert self.critic.max_limits == MAX_LIMITS
        assert self.critic.max_limits["diff_max"] == 1  # 개수 차이 최대 1 허용
        assert self.critic.max_limits["clearances_violation"] == 0

    def test_critique_pass_all(self):
        """TC-002: 모든 검증 통과 (완벽한 배치)"""
        placements = [
            PlacementResult(
                breaker_id="test",
                position={"x": 100, "y": 100, "row": 1, "col": 0},
                phase="L1",
                current_a=20,
                poles=2,
            )
        ]

        result = self.critic.critique(
            placements=placements,
            diff_max=0,  # 완벽한 균등
            clearance_violations=0,
        )

        assert result.passed is True
        assert result.score == 100
        assert len(result.violations) == 0
        assert len(result.warnings) == 0

    def test_critique_phase_imbalance_violation(self):
        """TC-003: 상평형 위반 감지 (diff_max > 1)"""
        placements = [
            PlacementResult(
                breaker_id="test",
                position={"x": 100, "y": 100, "row": 1, "col": 0},
                phase="L1",
                current_a=20,
                poles=2,
            )
        ]

        # diff_max=3 > 1 위반
        result = self.critic.critique(
            placements=placements,
            diff_max=3,
            clearance_violations=0,
        )

        assert result.passed is False
        assert len(result.violations) == 1
        assert "diff_max=3" in result.violations[0]
        assert result.score == 80  # 1개 위반 = -20점

    def test_critique_phase_imbalance_allowed(self):
        """TC-004: 상평형 허용 (diff_max = 1)"""
        placements = [
            PlacementResult(
                breaker_id="test",
                position={"x": 100, "y": 100, "row": 1, "col": 0},
                phase="L1",
                current_a=20,
                poles=2,
            )
        ]

        # diff_max=1은 허용 범위
        result = self.critic.critique(
            placements=placements,
            diff_max=1,
            clearance_violations=0,
        )

        assert result.passed is True
        assert len(result.violations) == 0
        assert result.score == 100

    def test_critique_clearance_violation(self):
        """TC-005: 간섭 위반 감지"""
        placements = [
            PlacementResult(
                breaker_id="b1",
                position={"x": 100, "y": 100, "row": 1, "col": 0},
                phase="L1",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="b2",
                position={"x": 120, "y": 100, "row": 1, "col": 1},
                phase="L1",
                current_a=20,
                poles=2,
            ),
        ]

        result = self.critic.critique(
            placements=placements,
            diff_max=0,
            clearance_violations=2,
        )

        assert result.passed is False
        assert any("clearance" in v.lower() for v in result.violations)

    def test_critique_position_violation(self):
        """TC-009: 위치 경계 위반"""
        placements = [
            PlacementResult(
                breaker_id="bad_position",
                position={"x": 100, "y": 100, "row": 25, "col": 0},
                phase="L1",
                current_a=20,
                poles=2,
            )
        ]

        result = self.critic.critique(
            placements=placements,
            diff_max=0,
            clearance_violations=0,
        )

        assert result.passed is False
        assert any("invalid row" in v.lower() for v in result.violations)

    def test_critique_multiple_violations(self):
        """TC-010: 복수 위반 동시 발생"""
        placements = [
            PlacementResult(
                breaker_id="bad_placement",
                position={"x": 100, "y": 100, "row": 25, "col": 0},
                phase="L1",
                current_a=300,
                poles=3,
            )
        ]

        # diff_max=5 위반 + 간섭 3개 + 위치 위반
        result = self.critic.critique(
            placements=placements,
            diff_max=5,
            clearance_violations=3,
        )

        assert result.passed is False
        assert len(result.violations) >= 3
        # 3개 위반 = -60점 → 40점 이하
        assert result.score <= 40

    def test_critique_empty_placements_forbidden(self):
        """TC-011: 빈 입력 금지 (목업 금지 원칙)"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        with pytest.raises(EstimatorError):
            self.critic.critique(
                placements=[],
                diff_max=0,
                clearance_violations=0,
            )

    def test_critique_score_calculation(self):
        """TC-012: 점수 계산 로직 검증"""
        placements = [
            PlacementResult(
                breaker_id="test",
                position={"x": 100, "y": 100, "row": 1, "col": 0},
                phase="L1",
                current_a=20,
                poles=2,
            )
        ]

        # diff_max=3 > 1 → 1개 위반 = -20점
        result = self.critic.critique(
            placements=placements,
            diff_max=3,
            clearance_violations=0,
        )
        assert result.score == 80

        # diff_max=0 완벽 → 100점
        result2 = self.critic.critique(
            placements=placements,
            diff_max=0,
            clearance_violations=0,
        )
        assert result2.score == 100

    def test_generate_svg_evidence(self):
        """TC-013: SVG Evidence 생성"""
        placements = [
            PlacementResult(
                breaker_id="test",
                position={"x": 100, "y": 100, "row": 1, "col": 0},
                phase="L1",
                current_a=20,
                poles=2,
            )
        ]

        result = self.critic.critique(
            placements=placements,
            diff_max=0,
            clearance_violations=0,
        )

        svg_content = self.critic.generate_svg_evidence(result)
        assert "<svg" in svg_content
        assert "PASSED" in svg_content
        assert "Phase Imbalance" in svg_content

    def test_violation_details_structure(self):
        """TC-014: ViolationDetail 구조 검증"""
        placements = [
            PlacementResult(
                breaker_id="test",
                position={"x": 100, "y": 100, "row": 1, "col": 0},
                phase="L1",
                current_a=20,
                poles=2,
            )
        ]

        # diff_max=3 > 1 위반
        result = self.critic.critique(
            placements=placements,
            diff_max=3,
            clearance_violations=0,
        )

        assert len(result.violation_details) > 0
        detail = result.violation_details[0]
        assert detail.type == "phase_count_imbalance"
        assert detail.severity == "critical"
        assert detail.message is not None
        assert detail.cause is not None
        assert detail.recommendation is not None
        assert detail.value == 3
        assert detail.limit == 1

    def test_metrics_output(self):
        """TC-015: Metrics 출력 검증"""
        placements = [
            PlacementResult(
                breaker_id="b1",
                position={"x": 100, "y": 100, "row": 1, "col": 0},
                phase="L1",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="b2",
                position={"x": 200, "y": 100, "row": 1, "col": 1},
                phase="L1",
                current_a=30,
                poles=2,
            ),
        ]

        result = self.critic.critique(
            placements=placements,
            diff_max=0,
            clearance_violations=0,
        )

        assert result.metrics["diff_max"] == 0
        assert result.metrics["clearance_violations"] == 0
        assert result.metrics["slot_count"] == 2
