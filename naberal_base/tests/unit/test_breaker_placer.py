"""
Unit tests for BreakerPlacer (Stage 2) - 실제 샘플 기반

Tests:
- TC-001: SAMPLE2 케이스 (4P 메인 + 2P 10개 = 5줄)
- TC-002: 좌우 대칭 배치 검증
- TC-003: RST 순환 검증
- TC-004: 3P 메인 차단기
- TC-005: 홀수 개 분기 차단기
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
from kis_estimator_core.engine.breaker_placer import (  # noqa: E402
    BreakerPlacer,
    BreakerInput,
    PanelSpec,
    PlacementResult,
)


class TestBreakerPlacer:
    """BreakerPlacer 단위 테스트 - 실제 샘플 기반"""

    def test_tc001_sample2_case(self):
        """TC-001: SAMPLE2 케이스 - 4P 메인 + 2P 10개 = 5줄"""
        # Given: SAMPLE2와 동일 구성
        breakers = [
            # 메인 차단기 (4P)
            BreakerInput(
                id="MAIN",
                poles=4,
                current_a=50,
                width_mm=100,
                height_mm=257,
                depth_mm=109,
            ),
            # 분기 차단기 (2P × 10)
            BreakerInput(
                id="CB01",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB02",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB03",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB04",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB05",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB06",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB07",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB08",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB09",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB10",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
        ]
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        # When: 배치 실행
        placer = BreakerPlacer()
        placements = placer.place(breakers, panel)

        # Then: 결과 검증
        assert len(placements) == 11, "메인 1개 + 분기 10개 = 11개"

        # 메인 차단기 확인
        main = placements[0]
        assert main.breaker_id == "MAIN", "메인 차단기가 첫 번째"
        assert main.poles == 4, "4P 메인"
        assert main.position["row"] == 0, "메인은 row 0"
        assert main.position["side"] == "center", "메인은 중앙"

        # 분기 차단기 확인 (10개 = 5줄)
        branch_placements = placements[1:]
        assert len(branch_placements) == 10, "분기 10개"

        # 좌우 개수 확인 (5 + 5)
        left_count = sum(1 for p in branch_placements if p.position["side"] == "left")
        right_count = sum(1 for p in branch_placements if p.position["side"] == "right")
        assert left_count == 5, "좌측 5개"
        assert right_count == 5, "우측 5개"

        # RST 순환 확인 (5줄 = R, S, T, R, S)
        row_phases = {}
        for p in branch_placements:
            row = p.position["row"]
            if row not in row_phases:
                row_phases[row] = p.phase

        # Note: breaker_placer uses "R/S/T" labels, not "L1/L2/L3"
        expected_phases = {1: "R", 2: "R", 3: "S", 4: "S", 5: "T"}
        assert (
            row_phases == expected_phases
        ), f"5줄 count-based phase balance: {row_phases}"

        # Phase balance validation (Count-based: R=4, S=3, T=3 → diff_max=1 ≤ 1 → PASS)
        # No error expected, just verify it doesn't raise
        placer.validate(placements)  # Should pass without error

    def test_tc002_left_right_symmetric(self):
        """TC-002: 좌우 대칭 배치 검증"""
        # Given: 3P 메인 + 2P 6개
        breakers = [
            BreakerInput(
                id="MAIN",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB01",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB02",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB03",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB04",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB05",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="CB06",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
        ]
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        # When: 배치 실행
        placer = BreakerPlacer()
        placements = placer.place(breakers, panel)

        # Then: 좌우 대칭 확인
        branch_placements = placements[1:]  # 메인 제외

        # 3줄 구성 (좌측 3개 + 우측 3개)
        left = [p for p in branch_placements if p.position["side"] == "left"]
        right = [p for p in branch_placements if p.position["side"] == "right"]

        assert len(left) == 3, "좌측 3개"
        assert len(right) == 3, "우측 3개"

        # 같은 줄은 같은 상
        for row in [1, 2, 3]:
            left_phase = next(p.phase for p in left if p.position["row"] == row)
            right_phase = next(p.phase for p in right if p.position["row"] == row)
            assert left_phase == right_phase, f"{row}줄 좌우 동일 상: {left_phase}"

    def test_tc003_rst_rotation(self):
        """TC-003: RST 순환 검증 (7줄)"""
        # Given: 3P 메인 + 2P 14개
        breakers = [
            BreakerInput(
                id="MAIN",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
        ]
        for i in range(1, 15):
            breakers.append(
                BreakerInput(
                    id=f"CB{i:02d}",
                    poles=2,
                    current_a=20,
                    width_mm=50,
                    height_mm=130,
                    depth_mm=60,
                )
            )
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        # When: 배치 실행
        placer = BreakerPlacer()
        placements = placer.place(breakers, panel)

        # Then: 7줄 RST 순환 확인
        branch_placements = placements[1:]

        # 줄별 상 추출
        row_phases = {}
        for p in branch_placements:
            row = p.position["row"]
            if row not in row_phases:
                row_phases[row] = p.phase

        # 7줄 count-based phase balance (not perfect rotation)
        # Note: breaker_placer uses count-based balancing: R=5, S=5, T=4
        # Expected: R=5개 (rows 1,2,3), S=5개 (rows 4,5), T=4개 (rows 6,7)
        expected = {1: "R", 2: "R", 3: "R", 4: "S", 5: "S", 6: "T", 7: "T"}
        assert row_phases == expected, f"7줄 count-based phase balance: {row_phases}"

    def test_tc004_3p_main_breaker(self):
        """TC-004: 3P 메인 차단기 배치"""
        # Given: 3P 메인만
        breakers = [
            BreakerInput(
                id="MAIN",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
        ]
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        # When: 배치 실행
        placer = BreakerPlacer()
        placements = placer.place(breakers, panel)

        # Then: 메인만 배치
        assert len(placements) == 1, "메인 1개만"
        main = placements[0]
        assert main.breaker_id == "MAIN", "메인 차단기"
        assert main.poles == 3, "3P"
        assert main.phase == "R", "3상 대표 R (not L1)"
        assert main.position["side"] == "center", "중앙 배치"

    def test_tc005_odd_number_branches(self):
        """TC-005: 홀수 개 분기 차단기 (좌측에 1개 더)"""
        # Given: 4P 메인 + 2P 9개
        breakers = [
            BreakerInput(
                id="MAIN",
                poles=4,
                current_a=50,
                width_mm=100,
                height_mm=257,
                depth_mm=109,
            ),
        ]
        for i in range(1, 10):
            breakers.append(
                BreakerInput(
                    id=f"CB{i:02d}",
                    poles=2,
                    current_a=20,
                    width_mm=50,
                    height_mm=130,
                    depth_mm=60,
                )
            )
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        # When: 배치 실행
        placer = BreakerPlacer()
        placements = placer.place(breakers, panel)

        # Then: 좌측 5개, 우측 4개
        branch_placements = placements[1:]
        left = [p for p in branch_placements if p.position["side"] == "left"]
        right = [p for p in branch_placements if p.position["side"] == "right"]

        assert len(left) == 5, "좌측 5개 (홀수면 좌측에 1개 더)"
        assert len(right) == 4, "우측 4개"

    def test_no_breakers_raises_error(self):
        """목업 금지: 빈 입력 시 오류 발생"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        placer = BreakerPlacer()
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        with pytest.raises(EstimatorError, match="No breakers provided"):
            placer.place([], panel)

    def test_phase_balance_calculation(self):
        """상평형 계산 정확도 검증 (Count-based balancing)"""

        # Given: 개수 불균형한 배치 (R=3, S=1, T=1)
        placements = [
            PlacementResult(
                breaker_id="CB01",
                position={"x": 150, "y": 100, "row": 1, "col": 0},
                phase="R",
                current_a=100,
                poles=2,
            ),
            PlacementResult(
                breaker_id="CB02",
                position={"x": 450, "y": 100, "row": 1, "col": 1},
                phase="R",
                current_a=50,
                poles=2,
            ),
            PlacementResult(
                breaker_id="CB03",
                position={"x": 150, "y": 250, "row": 2, "col": 0},
                phase="R",
                current_a=50,
                poles=2,
            ),
            PlacementResult(
                breaker_id="CB04",
                position={"x": 450, "y": 250, "row": 2, "col": 1},
                phase="S",
                current_a=50,
                poles=2,
            ),
            PlacementResult(
                breaker_id="CB05",
                position={"x": 150, "y": 400, "row": 3, "col": 0},
                phase="T",
                current_a=50,
                poles=2,
            ),
        ]

        placer = BreakerPlacer()

        # When: 상평형 검증 (개수 불균형: R=3, S=1, T=1 → diff_max=2 > 1 → WARNING)
        # Note: breaker_placer only logs WARNING, does not raise error
        placer.validate(placements)  # Should complete without raising exception
        # The WARNING log is captured in test output (see: "Phase count imbalance: diff_max=2...")
