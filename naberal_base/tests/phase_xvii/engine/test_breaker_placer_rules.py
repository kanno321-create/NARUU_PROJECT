"""
Phase XVII - Breaker Placer Rules Tests (≥8 tests)

Coverage Target: branch bus mapping, phase imbalance guard edges, placement rules
Zero-Mock: SSOT mini-data stubs only (no catalog/network calls)
"""

import pytest
from kis_estimator_core.engine.breaker_placer import (
    BreakerPlacer,
    BreakerInput,
    PanelSpec,
)


@pytest.mark.unit
class TestBranchBusMapping:
    """Test branch bus mapping logic (좌우 대칭 배치)"""

    def test_branch_bus_left_right_symmetry(self):
        """분기 차단기 좌우 대칭 배치"""
        placer = BreakerPlacer()
        breakers = [
            BreakerInput(
                id="main",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="b1", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
            ),
            BreakerInput(
                id="b2", poles=2, current_a=30, width_mm=50, height_mm=130, depth_mm=60
            ),
        ]
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        placements = placer.place(breakers, panel)

        # 메인(row=0) + 분기(row≥1)
        main_placements = [p for p in placements if p.position.get("row") == 0]
        branch_placements = [p for p in placements if p.position.get("row") >= 1]

        assert len(main_placements) == 1  # 메인 1개
        assert len(branch_placements) == 2  # 분기 2개

        # 좌우 대칭: 2개 분기 → 1개 좌측, 1개 우측
        left_branches = [
            p for p in branch_placements if p.position.get("side") == "left"
        ]
        right_branches = [
            p for p in branch_placements if p.position.get("side") == "right"
        ]
        assert len(left_branches) == 1
        assert len(right_branches) == 1

    def test_branch_bus_phase_assignment_roundrobin(self):
        """R→S→T 라운드로빈 상 배정"""
        placer = BreakerPlacer()
        breakers = [
            BreakerInput(
                id="main",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="b1", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
            ),
            BreakerInput(
                id="b2", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
            ),
            BreakerInput(
                id="b3", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
            ),
        ]
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        placements = placer.place(breakers, panel)

        # 분기 3개 → R, S, T 각 1개씩
        branch_placements = [p for p in placements if p.position.get("row") >= 1]
        phases = [p.phase for p in branch_placements]

        # 3개 분기 → R/S/T 각 1개씩 (완전 균등)
        assert phases.count("R") == 1
        assert phases.count("S") == 1
        assert phases.count("T") == 1


@pytest.mark.unit
class TestPhaseImbalanceGuard:
    """Test phase imbalance guard edge cases (개수 기반)"""

    def test_phase_balance_perfect_3_breakers(self):
        """완벽한 상평형: 3개 분기 (R/S/T 각 1개)"""
        placer = BreakerPlacer()
        breakers = [
            BreakerInput(
                id="main",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="b1", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
            ),
            BreakerInput(
                id="b2", poles=2, current_a=30, width_mm=50, height_mm=130, depth_mm=60
            ),
            BreakerInput(
                id="b3", poles=2, current_a=40, width_mm=50, height_mm=130, depth_mm=60
            ),
        ]
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        placements = placer.place(breakers, panel)
        result = placer.validate(placements)

        # diff_max = 0 (완벽한 균등)
        assert result.phase_imbalance_pct == 0.0
        assert result.clearance_violations == 0
        assert result.is_valid

    def test_phase_balance_edge_4_breakers(self):
        """4개 분기 → R=2, S=1, T=1 (diff_max=1, PASS)"""
        placer = BreakerPlacer()
        breakers = [
            BreakerInput(
                id="main",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="b1", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
            ),
            BreakerInput(
                id="b2", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
            ),
            BreakerInput(
                id="b3", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
            ),
            BreakerInput(
                id="b4", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
            ),
        ]
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        placements = placer.place(breakers, panel)
        result = placer.validate(placements)

        # diff_max ≤ 1 (TARGET)
        assert result.phase_imbalance_pct <= 1.0
        # clearance 위반 없음
        assert result.clearance_violations == 0

    def test_phase_balance_edge_9_breakers(self):
        """9개 분기 → R=3, S=3, T=3 (diff_max=0, 완벽)"""
        placer = BreakerPlacer()
        breakers = [
            BreakerInput(
                id="main",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            )
        ]
        for i in range(9):
            breakers.append(
                BreakerInput(
                    id=f"b{i+1}",
                    poles=2,
                    current_a=20,
                    width_mm=50,
                    height_mm=130,
                    depth_mm=60,
                )
            )
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        placements = placer.place(breakers, panel)
        result = placer.validate(placements)

        # 9개 → 각 3개씩 완벽 분배
        assert result.phase_imbalance_pct == 0.0
        assert result.is_valid


@pytest.mark.unit
class TestPlacementRules:
    """Test placement rules for different breaker frame AF sizes"""

    def test_main_breaker_center_top_position(self):
        """메인 차단기 상단 중앙 배치"""
        placer = BreakerPlacer()
        breakers = [
            BreakerInput(
                id="main",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="b1", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
            ),
        ]
        panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

        placements = placer.place(breakers, panel)

        main = [p for p in placements if p.breaker_id == "main"][0]
        # 상단 중앙: row=0, side=center
        assert main.position["row"] == 0
        assert main.position["side"] == "center"
        # x = 패널 폭 / 2
        assert main.position["x"] == panel.width_mm // 2

    def test_4p_n_phase_metadata_shared(self):
        """4P 차단기 마주보기 배치 시 N상 shared metadata"""
        placer = BreakerPlacer()
        breakers = [
            BreakerInput(
                id="main",
                poles=4,
                current_a=100,
                width_mm=100,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="b1", poles=4, current_a=50, width_mm=100, height_mm=130, depth_mm=60
            ),
            BreakerInput(
                id="b2", poles=4, current_a=50, width_mm=100, height_mm=130, depth_mm=60
            ),
        ]
        panel = PanelSpec(width_mm=700, height_mm=1200, depth_mm=200, clearance_mm=50)

        placements = placer.place(breakers, panel)

        # 분기 4P 2개 (마주보기)
        branch_4p = [
            p for p in placements if p.poles == 4 and p.position.get("row") >= 1
        ]
        assert len(branch_4p) == 2

        # 둘 다 n_bus_metadata.n_bus_type == "shared" (shared_if_pair 규칙)
        for p in branch_4p:
            metadata = p.position.get("n_bus_metadata", {})
            assert metadata["n_bus_type"] == "shared"
            assert metadata["n_bus_side"] == "center"
            assert metadata["rule"] == "shared_if_pair"

    def test_4p_n_phase_metadata_split(self):
        """4P 차단기 단독 배치 시 N상 split metadata"""
        placer = BreakerPlacer()
        breakers = [
            BreakerInput(
                id="main",
                poles=4,
                current_a=100,
                width_mm=100,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="b1", poles=4, current_a=50, width_mm=100, height_mm=130, depth_mm=60
            ),
        ]
        panel = PanelSpec(width_mm=700, height_mm=1200, depth_mm=200, clearance_mm=50)

        placements = placer.place(breakers, panel)

        # 분기 4P 1개 (단독)
        branch_4p = [
            p for p in placements if p.poles == 4 and p.position.get("row") >= 1
        ]
        assert len(branch_4p) == 1

        # n_bus_metadata.n_bus_type == "split" (split_if_single 규칙)
        metadata = branch_4p[0].position.get("n_bus_metadata", {})
        assert metadata["n_bus_type"] == "split"
        assert "only" in metadata["n_bus_side"]  # left_only or right_only
        assert metadata["rule"] == "split_if_single"
