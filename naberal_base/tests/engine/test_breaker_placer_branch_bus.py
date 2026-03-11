"""
KIS Branch/Bus Rules Integration Tests for breaker_placer.py

이 테스트는 breaker_placer.py가 SSOT Branch/Bus Rules를 올바르게 적용하는지 검증합니다.

검증 항목:
1. 3P 다수 + 4P 혼합 배치 (center-feed, bolt_integrity)
2. 4P×4개 연속 배치 (중간 N상 마주보기, shared_if_pair)
3. 첫/마지막 N상 center-feed 연결 (split_if_single)
4. N 크로스 금지 위반 시 FAIL (no_cross_link)
5. 볼트 규격 불일치 FAIL (bolt_integrity)
"""

import pytest


# from kis_estimator_core.engine.breaker_placer import BreakerPlacer
# from kis_estimator_core.engine.breaker_placer import BreakerInput, PanelSpec, PlacementResult


def test_case_a_3p_and_4p_mixed_placement():
    """
    케이스 A: 3P 다수 + 4P 혼합 배치

    검증:
    - center-feed 방향 (downward_from_main_mccb)
    - bolt_integrity (상별 볼트 결합)
    - outputs_outer_only (2차 단자 외측만)

    기대:
    - 모든 validation_guards PASS
    - 배치 시간 < 0.3s
    """
    import sys
    import time

    sys.path.insert(0, "src")
    from kis_estimator_core.engine.breaker_placer import (
        BreakerPlacer,
        BreakerInput,
        PanelSpec,
    )

    placer = BreakerPlacer()
    breakers = [
        BreakerInput(
            id="MAIN", poles=3, current_a=100, width_mm=75, height_mm=130, depth_mm=60
        ),
        BreakerInput(
            id="CB01", poles=3, current_a=50, width_mm=75, height_mm=130, depth_mm=60
        ),
        BreakerInput(
            id="CB02", poles=4, current_a=30, width_mm=100, height_mm=130, depth_mm=60
        ),
        BreakerInput(
            id="CB03", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
        ),
        BreakerInput(
            id="CB04", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
        ),
        BreakerInput(
            id="CB05", poles=2, current_a=20, width_mm=50, height_mm=130, depth_mm=60
        ),
    ]
    panel = PanelSpec(width_mm=600, height_mm=800, depth_mm=200, clearance_mm=50)

    start = time.time()
    placements = placer.place(breakers, panel)
    elapsed = time.time() - start

    # 배치 시간 검증
    assert elapsed < 0.3, f"Placement took {elapsed:.3f}s > 0.3s"

    # 검증 실행
    _ = placer.validate(placements)

    # Validation guards 검증
    branch_bus_violations = placer._validate_branch_bus_rules(placements)
    assert (
        len(branch_bus_violations) == 0
    ), f"Branch Bus Rules violations: {branch_bus_violations}"

    # 메인 차단기 center-feed 검증
    main_placement = [p for p in placements if p.breaker_id == "MAIN"][0]
    assert main_placement.position.get("side") == "center", "Main breaker not at center"

    # 4P 차단기 n_bus_metadata 존재 확인
    cb02_placement = [p for p in placements if p.breaker_id == "CB02"][0]
    assert (
        "n_bus_metadata" in cb02_placement.position
    ), "4P breaker missing n_bus_metadata"

    print(f"[PASS] Test case A: 3P+4P mixed placement (elapsed={elapsed:.3f}s)")


def test_case_b_4p_consecutive_shared_n_phase():
    """
    케이스 B: 4P×4개 연속 배치 (중간 N상 마주보기)

    검증:
    - shared_if_pair: 마주보는 4P들의 N상은 하나의 분기부스바 공유
    - n_phase_rightmost: N상은 항상 최우측 컬럼

    기대:
    - 모든 4P 쌍이 마주보기로 배치 (shared_n_bus)
    - 좌우 N상 간 cross link 없음 (no_cross_link)

    배치: left=[CB01, CB03], right=[CB02, CB04]
    - row 1: CB01 (left) <-> CB02 (right)
    - row 2: CB03 (left) <-> CB04 (right)
    """
    import sys

    sys.path.insert(0, "src")
    from kis_estimator_core.engine.breaker_placer import (
        BreakerPlacer,
        BreakerInput,
        PanelSpec,
    )

    placer = BreakerPlacer()
    breakers = [
        BreakerInput(
            id="MAIN", poles=4, current_a=100, width_mm=100, height_mm=130, depth_mm=60
        ),
        BreakerInput(
            id="CB01", poles=4, current_a=30, width_mm=100, height_mm=130, depth_mm=60
        ),
        BreakerInput(
            id="CB02", poles=4, current_a=30, width_mm=100, height_mm=130, depth_mm=60
        ),
        BreakerInput(
            id="CB03", poles=4, current_a=30, width_mm=100, height_mm=130, depth_mm=60
        ),
        BreakerInput(
            id="CB04", poles=4, current_a=30, width_mm=100, height_mm=130, depth_mm=60
        ),
    ]
    panel = PanelSpec(width_mm=600, height_mm=1200, depth_mm=200, clearance_mm=50)

    placements = placer.place(breakers, panel)
    placer.validate(placements)

    # 4P 배치 확인 (좌우 대칭: left=[CB01, CB03], right=[CB02, CB04])
    cb01_placement = [p for p in placements if p.breaker_id == "CB01"][0]
    cb02_placement = [p for p in placements if p.breaker_id == "CB02"][0]
    cb03_placement = [p for p in placements if p.breaker_id == "CB03"][0]
    cb04_placement = [p for p in placements if p.breaker_id == "CB04"][0]

    # n_bus_metadata 확인 (모두 shared_if_pair - 모두 마주보는 쌍 있음)
    cb01_metadata = cb01_placement.position.get("n_bus_metadata", {})
    cb02_metadata = cb02_placement.position.get("n_bus_metadata", {})
    cb03_metadata = cb03_placement.position.get("n_bus_metadata", {})
    cb04_metadata = cb04_placement.position.get("n_bus_metadata", {})

    # 모든 4P가 shared_if_pair 규칙 적용 (모두 pair 있음)
    assert (
        cb01_metadata.get("n_bus_type") == "shared"
    ), f"CB01 n_bus_type={cb01_metadata.get('n_bus_type')}, expected shared"
    assert (
        cb02_metadata.get("n_bus_type") == "shared"
    ), f"CB02 n_bus_type={cb02_metadata.get('n_bus_type')}, expected shared"
    assert (
        cb03_metadata.get("n_bus_type") == "shared"
    ), f"CB03 n_bus_type={cb03_metadata.get('n_bus_type')}, expected shared"
    assert (
        cb04_metadata.get("n_bus_type") == "shared"
    ), f"CB04 n_bus_type={cb04_metadata.get('n_bus_type')}, expected shared"

    # N상 간섭 위반 없음 (LAY-004)
    n_phase_violations = placer._validate_4p_n_phase_interference(placements)
    assert n_phase_violations == 0, f"N-phase violations: {n_phase_violations}"

    print("[PASS] Test case B: 4P consecutive shared N-phase")


def test_case_c_first_last_n_phase_split():
    """
    케이스 C: 첫/마지막 N상 center-feed 연결

    검증:
    - split_if_single: 쌍이 없는 4P의 N상은 center에서 따로 연결
    - shared_if_pair: 마주보는 쌍이 있으면 공유

    기대 (홀수 개 4P):
    - CB01: 쌍 있음 → shared
    - CB02: 단독 (left row 2) → split
    - CB03: 쌍 있음 → shared

    배치: 3개 4P → left=[CB01, CB02], right=[CB03]
    - row 1: CB01 (left) <-> CB03 (right) → shared
    - row 2: CB02 (left) 단독 → split
    """
    import sys

    sys.path.insert(0, "src")
    from kis_estimator_core.engine.breaker_placer import (
        BreakerPlacer,
        BreakerInput,
        PanelSpec,
    )

    placer = BreakerPlacer()
    breakers = [
        BreakerInput(
            id="MAIN", poles=4, current_a=100, width_mm=100, height_mm=130, depth_mm=60
        ),
        BreakerInput(
            id="CB01", poles=4, current_a=30, width_mm=100, height_mm=130, depth_mm=60
        ),  # left, pair 있음
        BreakerInput(
            id="CB02", poles=4, current_a=30, width_mm=100, height_mm=130, depth_mm=60
        ),  # left, 단독
        BreakerInput(
            id="CB03", poles=4, current_a=30, width_mm=100, height_mm=130, depth_mm=60
        ),  # right, pair 있음
    ]
    panel = PanelSpec(width_mm=600, height_mm=1500, depth_mm=200, clearance_mm=50)

    placements = placer.place(breakers, panel)
    placer.validate(placements)

    # 3개 4P 배치 확인: left=[CB01, CB02], right=[CB03]
    cb01_placement = [p for p in placements if p.breaker_id == "CB01"][0]
    cb02_placement = [p for p in placements if p.breaker_id == "CB02"][0]
    cb03_placement = [p for p in placements if p.breaker_id == "CB03"][0]

    cb01_metadata = cb01_placement.position.get("n_bus_metadata", {})
    cb02_metadata = cb02_placement.position.get("n_bus_metadata", {})
    cb03_metadata = cb03_placement.position.get("n_bus_metadata", {})

    # CB01-CB03: 마주보는 쌍 → shared_if_pair
    assert (
        cb01_metadata.get("n_bus_type") == "shared"
    ), f"CB01 n_bus_type={cb01_metadata.get('n_bus_type')}, expected shared"
    assert (
        cb03_metadata.get("n_bus_type") == "shared"
    ), f"CB03 n_bus_type={cb03_metadata.get('n_bus_type')}, expected shared"

    # CB02: 단독 (홀수 개, left row 2) → split_if_single
    assert (
        cb02_metadata.get("n_bus_type") == "split"
    ), f"CB02 n_bus_type={cb02_metadata.get('n_bus_type')}, expected split"
    assert (
        cb02_metadata.get("rule") == "split_if_single"
    ), f"CB02 rule={cb02_metadata.get('rule')}"

    print("[PASS] Test case C: first/last N-phase split")


@pytest.mark.skip(
    reason="TODO: Implement 4P N-phase row-aware logic in breaker_placer.py"
)
def test_case_d_n_cross_link_violation_fail():
    """
    케이스 D: N 크로스 금지 위반 시 FAIL

    검증:
    - no_cross_link: N상 간 횡연결 금지

    기대:
    - ValidationError 발생
    - 에러 코드: LAYOUT_RULE_VIOLATION
    - meta: {rule: "n_no_cross_link", phase: "N"}
    """

    # placer = BreakerPlacer()
    #
    # # 인위적으로 N상 크로스 링크 유도 (테스트용 mock)
    # # 실제로는 breaker_placer.py가 이를 방지해야 함
    #
    # # 예상: ValidationError 발생
    # with pytest.raises(ValidationError) as exc_info:
    #     # ... N 크로스 링크 유발 배치 시도
    #     pass
    #
    # error = exc_info.value
    # assert "LAYOUT_RULE_VIOLATION" in str(error)
    # assert error.meta["rule"] == "n_no_cross_link"
    # assert error.meta["phase"] == "N"
    pass


@pytest.mark.skip(
    reason="TODO: Implement 4P N-phase row-aware logic in breaker_placer.py"
)
def test_case_e_bolt_integrity_violation_fail():
    """
    케이스 E: 볼트 규격 불일치 FAIL

    검증:
    - bolt_integrity: 상별 볼트 규격 일치 강제

    기대:
    - ValidationError 발생
    - 에러 코드: LAYOUT_RULE_VIOLATION
    - meta: {rule: "bolt_integrity", phase: "R/S/T/N"}
    """

    # placer = BreakerPlacer()
    #
    # # 인위적으로 볼트 규격 불일치 유도 (테스트용 mock)
    # # 예: R상 분기부스바는 100AF인데 MAIN R은 50AF
    #
    # # 예상: ValidationError 발생
    # with pytest.raises(ValidationError) as exc_info:
    #     # ... 볼트 규격 불일치 유발 배치 시도
    #     pass
    #
    # error = exc_info.value
    # assert "LAYOUT_RULE_VIOLATION" in str(error)
    # assert error.meta["rule"] == "bolt_integrity"
    pass


def test_ssot_adapter_loads_successfully():
    """SSOT 어댑터가 정상적으로 로드되는지 검증"""
    from kis_estimator_core.core.ssot.branch_bus import (
        load_branch_bus_rules,
        get_validation_guards,
        get_n_phase_row_rules,
    )

    rules = load_branch_bus_rules()
    assert rules["meta"]["version"] == "1.0.0"
    assert rules["panel"]["layout"] == "center_feed_single_branch_bus"

    guards = get_validation_guards()
    assert guards["phase_alignment"] is True
    assert guards["bolt_integrity"] is True
    assert guards["n_no_cross_link"] is True
    assert guards["outputs_outer_only"] is True
    assert guards["center_feed_direction"] is True

    n_rules = get_n_phase_row_rules()
    assert n_rules["shared_if_pair"] is True
    assert n_rules["split_if_single"] is True
    assert n_rules["no_cross_link"] is True
    assert n_rules["n_phase_rightmost"] is True


def test_branch_bus_rules_loaded_in_placer():
    """BreakerPlacer가 Branch Bus Rules를 로드하는지 검증"""
    import sys

    sys.path.insert(0, "src")
    from kis_estimator_core.engine.breaker_placer import BreakerPlacer

    placer = BreakerPlacer()

    # Branch Bus Rules가 로드되었는지 확인
    assert hasattr(placer, "branch_bus_rules")
    assert hasattr(placer, "validation_guards")
    assert hasattr(placer, "n_phase_row_rules")

    # 규칙 내용 확인
    assert placer.branch_bus_rules["panel"]["layout"] == "center_feed_single_branch_bus"
    assert placer.validation_guards["n_no_cross_link"] is True
    assert placer.n_phase_row_rules["shared_if_pair"] is True
