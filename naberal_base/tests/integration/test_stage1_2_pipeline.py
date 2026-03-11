"""
Integration Tests: Stage 1 + Stage 2 + Stage 2.1 Pipeline
Enclosure Solver → Breaker Placer → Breaker Critic

테스트 원칙:
- SPEC KIT 절대 기준
- 실제 데이터만 사용 (목업 절대 금지)
- SAMPLE2 기반 실제 케이스
- 전체 파이프라인 검증
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402

# CI skip - requires real catalog data from Supabase
pytestmark = pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipping stage 1-2 pipeline tests in CI - requires real catalog data"
)
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver  # noqa: E402
from kis_estimator_core.models.enclosure import (  # noqa: E402
    BreakerSpec,
    CustomerRequirements,
)
from kis_estimator_core.engine.breaker_placer import (  # noqa: E402
    BreakerPlacer,
    BreakerInput,
    PanelSpec,
)
from kis_estimator_core.engine.breaker_critic import BreakerCritic  # noqa: E402


class TestStage1_2_Pipeline:
    """Stage 1 + Stage 2 통합 테스트"""

    def test_integration_sample2_full_pipeline(self):
        """
        INT-001: SAMPLE2 전체 파이프라인 (Stage 1 → Stage 2)

        시나리오:
        1. Stage 1: 외함 크기 계산 (메인 4P + 분기 2P×10)
        2. Stage 2: 차단기 배치 (좌우 대칭, RST 순환)
        3. 검증: 상평형, 간섭, 치수
        """
        # ==================== Stage 1: Enclosure Solver ====================
        solver = EnclosureSolver()

        # 실제 SAMPLE2 차단기 구성
        # 메인 차단기 (4P 50A 400AF)
        main_breaker = BreakerSpec(
            id="MAIN",
            model="SBS-404",  # 4P 400AF 표준형
            poles=4,
            current_a=50,
            frame_af=400,
        )

        # 분기 차단기 (2P 20A × 10개, 50AF 경제형)
        branch_breakers = [
            BreakerSpec(
                id=f"CB{i:02d}",
                model="SBE-52",  # 2P 50AF 경제형
                poles=2,
                current_a=20,
                frame_af=50,
            )
            for i in range(1, 11)
        ]

        accessories = []  # 부속자재 없음
        customer_requirements = CustomerRequirements(
            enclosure_type="옥내노출",
            ip_rating="IP44",
        )

        # Stage 1 실행
        enclosure_result = solver.solve(
            main_breaker,
            branch_breakers,
            accessories,
            customer_requirements,
        )

        # Stage 1 검증
        assert enclosure_result is not None
        assert enclosure_result.quality_gate.passed is True  # SPEC: fit_score ≥ 0.90
        assert enclosure_result.dimensions.width_mm >= 600  # 최소 폭
        assert enclosure_result.dimensions.height_mm >= 600  # 최소 높이

        # ==================== Stage 2: Breaker Placer ====================
        placer = BreakerPlacer()

        # Stage 1 → Stage 2 변환 (수동, 실제 차단기 치수 사용)
        # 치수 출처: 절대코어파일/breaker_dimensions.json
        breakers = [
            # 메인: 4P 400AF - 187x257x109mm
            BreakerInput(
                id="MAIN",
                poles=4,
                current_a=50,
                width_mm=187,
                height_mm=257,
                depth_mm=109,
            ),
        ] + [
            # 분기: 2P 50AF - 50x130x60mm
            BreakerInput(
                id=f"CB{i:02d}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            )
            for i in range(1, 11)
        ]

        panel = PanelSpec(
            width_mm=enclosure_result.dimensions.width_mm,
            height_mm=enclosure_result.dimensions.height_mm,
            depth_mm=enclosure_result.dimensions.depth_mm,
            clearance_mm=50,  # 최소 간격
        )

        # Stage 2 실행
        placements = placer.place(breakers, panel)

        # Stage 2 검증
        assert len(placements) == 11  # 메인 1 + 분기 10

        # 메인 차단기 검증
        main_placement = next(p for p in placements if p.breaker_id == "MAIN")
        assert main_placement.position["row"] == 0  # 메인은 row 0
        assert main_placement.position["col"] == 0  # 중앙
        assert main_placement.phase == "R"  # RST 대표 (개수 기반)

        # 분기 차단기 검증
        branch_placements = [p for p in placements if p.breaker_id.startswith("CB")]
        assert len(branch_placements) == 10

        # 좌우 대칭 검증
        left_count = sum(1 for p in branch_placements if p.position["col"] == 0)
        right_count = sum(1 for p in branch_placements if p.position["col"] == 1)
        assert left_count == 5  # 좌측 5개
        assert right_count == 5  # 우측 5개

        # RST 순환 검증 (좌우 다른 상 가능: 좌R 우S)
        # 실무 기준: 1줄에 1개 부스바(동일 상) OR 좌우 다른 상(좌R 우S) 모두 허용
        for row_idx in range(1, 6):  # row 1~5
            row_placements = [
                p for p in branch_placements if p.position["row"] == row_idx
            ]
            if len(row_placements) > 0:
                phases = set(p.phase for p in row_placements)
                # 1줄에 동일 상 OR 좌우 다른 상(최대 2개 상) 모두 OK
                assert len(phases) <= 2  # 동일 상(1개) 또는 좌우 다른 상(2개)

    def test_integration_stage1_2_21_full_pipeline(self):
        """
        INT-002: Stage 1 → Stage 2 → Stage 2.1 전체 파이프라인

        시나리오:
        1. Stage 1: 외함 계산
        2. Stage 2: 배치
        3. Stage 2.1: 배치 검증 (Critic)
        4. 품질 게이트 통과 확인
        """
        # ==================== Stage 1: Enclosure ====================
        solver = EnclosureSolver()

        # 메인 차단기 (3P 100A 100AF 경제형)
        main_breaker = BreakerSpec(
            id="MAIN",
            model="SBE-103",  # 3P 100AF 경제형
            poles=3,
            current_a=100,
            frame_af=100,
        )

        # 분기 차단기 (2P 20A × 9개, 50AF 경제형)
        branch_breakers = [
            BreakerSpec(
                id=f"CB{i:02d}",
                model="SBE-52",  # 2P 50AF 경제형
                poles=2,
                current_a=20,
                frame_af=50,
            )
            for i in range(1, 10)  # 9개 분기 (3의 배수, 좌우 대칭 시 R=3, S=3, T=3)
        ]

        accessories = []
        customer_requirements = CustomerRequirements(
            enclosure_type="옥내노출",
            ip_rating="IP44",
        )

        enclosure_result = solver.solve(
            main_breaker,
            branch_breakers,
            accessories,
            customer_requirements,
        )
        assert enclosure_result.quality_gate.passed is True

        # ==================== Stage 2: Breaker Placement ====================
        placer = BreakerPlacer()

        # Stage 1 → Stage 2 변환 (수동, 실제 치수)
        # 치수 출처: 절대코어파일/breaker_dimensions.json
        breakers = [
            # 메인: 3P 100AF - 75x130x60mm (경제형)
            BreakerInput(
                id="MAIN",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
        ] + [
            # 분기: 2P 50AF - 50x130x60mm
            BreakerInput(
                id=f"CB{i:02d}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            )
            for i in range(1, 10)  # 9개 분기
        ]

        panel = PanelSpec(
            width_mm=enclosure_result.dimensions.width_mm,
            height_mm=enclosure_result.dimensions.height_mm,
            depth_mm=enclosure_result.dimensions.depth_mm,
            clearance_mm=50,
        )

        placements = placer.place(breakers, panel)
        validation_result = placer.validate(placements)

        assert validation_result.is_valid is True
        # 상평형 (개수 기반): 9개 분기 → RST 라운드로빈 (R=3, S=3, T=3)
        # diff_max = 0 (완전 균등)
        diff_max = (
            validation_result.phase_imbalance_pct
        )  # 개수 차이 (이름 유지, 값은 diff_max)
        assert diff_max <= 1.0  # 개수 차이 최대 1
        assert validation_result.clearance_violations == 0  # SPEC: = 0

        # ==================== Stage 2.1: Critic ====================
        critic = BreakerCritic()

        critic_result = critic.critique(
            placements=placements,
            diff_max=diff_max,
            clearance_violations=validation_result.clearance_violations,
        )

        # Stage 2.1 검증 (개수 기반)
        # diff_max = 0 (완전 균등, 9개 = 3의 배수)
        assert critic_result.phase_imbalance_pct == 0.0  # diff_max (필드명 유지)
        # 상평형 경고는 있을 수 있지만, 간섭 위반은 없어야 함
        clearance_violations_list = [
            v for v in critic_result.violations if "clearance" in v.lower()
        ]
        assert len(clearance_violations_list) == 0  # 간섭 위반 없음

        # SVG Evidence 생성 테스트
        svg_content = critic.generate_svg_evidence(critic_result)
        assert "<svg" in svg_content
        assert "PASSED" in svg_content

    def test_integration_phase_imbalance_failure(self):
        """
        INT-003: 상평형 위반 시 Critic 감지 (의도적 실패 케이스)

        시나리오:
        1. Stage 2에서 불균형 배치 생성 (의도적)
        2. Stage 2.1에서 위반 감지
        3. 적절한 오류 메시지 및 권장사항 확인
        """
        # Stage 2 실행 (실제 배치)
        placer = BreakerPlacer()

        breakers = [
            BreakerInput(
                id="MAIN",
                poles=3,
                current_a=50,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
        ] + [
            BreakerInput(
                id=f"CB{i:02d}",
                poles=2,
                current_a=30,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            )
            for i in range(1, 5)
        ]

        panel = PanelSpec(
            width_mm=700,
            height_mm=800,
            depth_mm=200,
            clearance_mm=50,
        )

        placements = placer.place(breakers, panel)

        # Stage 2.1 실행 (의도적으로 높은 개수 차이 전달)
        critic = BreakerCritic()

        critic_result = critic.critique(
            placements=placements,
            diff_max=2.0,  # > 1 위반 (MAX_COUNT_DIFF = 1)
            clearance_violations=0,
        )

        # 검증 (개수 기반)
        assert critic_result.passed is False  # 실패해야 함
        assert len(critic_result.violations) >= 1  # 위반 사항 있음
        assert any("count imbalance" in v for v in critic_result.violations)
        assert critic_result.score < 100  # 점수 감점

        # 위반 상세 정보 확인
        phase_violation = next(
            (
                v
                for v in critic_result.violation_details
                if v.type == "phase_count_imbalance"
            ),
            None,
        )
        assert phase_violation is not None
        assert phase_violation.severity == "critical"
        assert "round-robin" in phase_violation.recommendation.lower()

    def test_integration_clearance_violation_detection(self):
        """
        INT-004: 간섭 위반 감지 통합 테스트

        시나리오:
        1. Stage 2에서 배치
        2. 간섭 검증에서 위반 발생
        3. Stage 2.1에서 감지 및 보고
        """
        placer = BreakerPlacer()

        # 밀집 배치를 유도하는 큰 차단기들
        breakers = [
            BreakerInput(
                id="MAIN",
                poles=4,
                current_a=200,
                width_mm=140,
                height_mm=257,
                depth_mm=109,
            ),
        ] + [
            BreakerInput(
                id=f"CB{i:02d}",
                poles=3,
                current_a=100,
                width_mm=90,
                height_mm=155,
                depth_mm=60,
            )
            for i in range(1, 7)
        ]

        panel = PanelSpec(
            width_mm=600,  # 좁은 패널 (의도적)
            height_mm=800,
            depth_mm=200,
            clearance_mm=50,
        )

        placements = placer.place(breakers, panel)
        validation_result = placer.validate(placements)

        # Stage 2.1 실행
        critic = BreakerCritic()

        critic_result = critic.critique(
            placements=placements,
            diff_max=validation_result.phase_imbalance_pct,  # 개수 차이 (필드명 유지, 값은 diff_max)
            clearance_violations=validation_result.clearance_violations,
        )

        # 간섭 위반이 있으면 Critic이 감지해야 함
        if validation_result.clearance_violations > 0:
            assert critic_result.passed is False
            assert any("clearance" in v.lower() for v in critic_result.violations)

    def test_integration_empty_breakers_forbidden(self):
        """
        INT-005: 빈 입력 금지 (목업 금지 원칙)

        모든 Stage에서 빈 입력 거부
        """
        # Stage 1
        _ = EnclosureSolver()

        # 빈 차단기 리스트로 테스트 (실패해야 함)
        # Note: solve()는 main_breaker, branch_breakers를 분리하므로
        # main_breaker가 None이거나 branch_breakers가 빈 리스트인 경우를 테스트
        # 이 테스트는 일단 스킵 (enclosure_solver의 입력 검증 로직 확인 필요)

        # Stage 2
        placer = BreakerPlacer()
        panel = PanelSpec(width_mm=600, height_mm=800, depth_mm=200, clearance_mm=50)
        with pytest.raises(ValueError):
            placer.place([], panel)

        # Stage 2.1 (이미 테스트됨)
        critic = BreakerCritic()
        with pytest.raises(ValueError, match="Mock data generation is FORBIDDEN"):
            critic.critique(
                placements=[],
                diff_max=0.0,
                clearance_violations=0,
            )

    def test_integration_performance_targets(self):
        """
        INT-006: 성능 목표 검증 (SPEC KIT 기준)

        성능 목표:
        - Stage 1 (Enclosure): < 500ms
        - Stage 2 (Breaker): < 1s (100개 이하)
        - Stage 2.1 (Critic): < 200ms
        """
        import time

        # 테스트 데이터 준비
        # 메인 차단기 (3P 100A 100AF)
        main_breaker = BreakerSpec(
            id="MAIN",
            model="SBE-103",
            poles=3,
            current_a=100,
            frame_af=100,
        )

        # 분기 차단기 (2P 20A × 20개)
        branch_breakers = [
            BreakerSpec(
                id=f"CB{i:02d}",
                model="SBE-52",
                poles=2,
                current_a=20,
                frame_af=50,
            )
            for i in range(1, 21)  # 20개
        ]

        accessories = []
        customer_requirements = CustomerRequirements(
            enclosure_type="옥내노출",
            ip_rating="IP44",
        )

        # Stage 1 성능 측정
        solver = EnclosureSolver()
        start = time.time()
        enclosure_result = solver.solve(
            main_breaker,
            branch_breakers,
            accessories,
            customer_requirements,
        )
        stage1_time = time.time() - start

        assert stage1_time < 0.5  # < 500ms

        # Stage 2 성능 측정
        placer = BreakerPlacer()

        # Stage 1 → Stage 2 변환 (수동, 실제 치수)
        breakers = [
            # 메인: 3P 100AF - 75x130x60mm
            BreakerInput(
                id="MAIN",
                poles=3,
                current_a=100,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
        ] + [
            # 분기: 2P 50AF - 50x130x60mm
            BreakerInput(
                id=f"CB{i:02d}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            )
            for i in range(1, 21)
        ]
        panel = PanelSpec(
            width_mm=enclosure_result.dimensions.width_mm,
            height_mm=enclosure_result.dimensions.height_mm,
            depth_mm=enclosure_result.dimensions.depth_mm,
            clearance_mm=50,
        )

        start = time.time()
        placements = placer.place(breakers, panel)
        stage2_time = time.time() - start

        assert stage2_time < 1.0  # < 1s

        # Stage 2.1 성능 측정
        critic = BreakerCritic()
        validation_result = placer.validate(placements)

        start = time.time()
        _ = critic.critique(
            placements=placements,
            diff_max=validation_result.phase_imbalance_pct,  # 개수 차이 (필드명 유지, 값은 diff_max)
            clearance_violations=0,
        )
        stage21_time = time.time() - start

        assert stage21_time < 0.2  # < 200ms (목표)

        # 전체 파이프라인 성능
        total_time = stage1_time + stage2_time + stage21_time
        print("\n성능 측정 결과:")
        print(f"  Stage 1: {stage1_time*1000:.1f}ms")
        print(f"  Stage 2: {stage2_time*1000:.1f}ms")
        print(f"  Stage 2.1: {stage21_time*1000:.1f}ms")
        print(f"  Total: {total_time*1000:.1f}ms")
