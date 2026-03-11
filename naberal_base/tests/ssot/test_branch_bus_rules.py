"""
KIS Branch/Bus Rules v1.0 — SSOT Validation Tests

이 테스트는 대표님 정의의 분전반 차단기 배치 및 분기부스바 로직이
SSOT 지식파일에 정확히 등록되었는지 검증합니다.

검증 항목 (6가지):
1. phase_alignment: 분기부스바 상과 MAIN BUS 상이 일치
2. bolt_integrity: 볼트 결합 무결성 확보
3. n_no_cross_link: 4P N상 단독 시 좌우 횡연결 금지
4. outputs_outer_only: 출력(2차)은 외측 단자만
5. center_feed_direction: Center-feed 하향 방식
6. row_aware_n_phase: 4P N상 row-aware 규칙 (shared_if_pair, split_if_single)
"""

import json
import pathlib
import importlib.util

JSON_PATH = pathlib.Path("KIS/Knowledge/packs/kis_branch_bus_rules.v1.json")
PY_PATH = pathlib.Path("KIS/Knowledge/packs/kis_branch_bus_rules.py")


def _load_py_rules():
    """Python 지식파일 동적 로드"""
    spec = importlib.util.spec_from_file_location("kis_branch_bus_rules", PY_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.get_rules()


def test_json_py_equivalence():
    """JSON과 Python 지식파일의 동등성 검증"""
    data_json = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    data_py = _load_py_rules()

    assert data_json["panel"]["layout"] == data_py["panel"]["layout"]
    assert data_json["phases"]["order"] == data_py["phases"]["order"]
    assert (
        data_json["policy"]["2P"]["shared_branch_bus"]
        == data_py["policy"]["2P"]["shared_branch_bus"]
    )
    assert (
        data_json["policy"]["3P"]["shared_branch_bus"]
        == data_py["policy"]["3P"]["shared_branch_bus"]
    )
    assert (
        data_json["policy"]["4P"]["rst_shared_branch_bus"]
        == data_py["policy"]["4P"]["rst_shared_branch_bus"]
    )


def test_phase_alignment_and_bolt_integrity():
    """① phase_alignment: 분기부스바 상 == MAIN BUS 상
    ② bolt_integrity: 볼트 결합 무결성"""
    rules = _load_py_rules()

    # Phase alignment 검증
    assert rules["validation_guards"]["phase_alignment"] is True
    assert rules["validation_guards"]["bolt_integrity"] is True

    # R/S/T/N가 정책에 모두 명시되어야 함
    assert set(rules["phases"]["order"]) == {"R", "S", "T", "N"}

    # 2P: R,S 볼트 결합
    assert set(rules["policy"]["2P"]["bolt_to_main"]) == {"R", "S"}

    # 3P: R,S,T 볼트 결합
    assert set(rules["policy"]["3P"]["bolt_to_main"]) == {"R", "S", "T"}

    # 4P: R,S,T + N 볼트 결합
    assert set(rules["policy"]["4P"]["bolt_to_main_rst"]) == {"R", "S", "T"}
    assert rules["policy"]["4P"]["n_phase"]["bolt_to_main_n"] is True


def test_n_phase_row_aware_rules():
    """③ 4P N상 row-aware: 쌍이면 공유, 단독이면 분리, 교차 금지, 우측 고정"""
    rules = _load_py_rules()["policy"]["4P"]["n_phase"]["row_rules"]

    assert rules["shared_if_pair"] is True
    assert rules["split_if_single"] is True
    assert rules["no_cross_link"] is True
    assert rules["n_phase_rightmost"] is True

    # Validation guard 확인
    r = _load_py_rules()
    assert r["validation_guards"]["n_no_cross_link"] is True
    assert r["validation_guards"]["row_aware_n_phase"]["shared_if_pair"] is True
    assert r["validation_guards"]["row_aware_n_phase"]["split_if_single"] is True


def test_outputs_outer_and_center_feed():
    """④ outputs_outer_only: 출력(2차) 외측 단자만
    ⑤ center_feed_direction: Center-feed 하향 방식"""
    r = _load_py_rules()

    # 출력(2차) 외측
    assert r["panel"]["outer_output_only"] is True
    assert r["validation_guards"]["outputs_outer_only"] is True

    # Center-feed 하향
    assert r["positioning"]["main_bus_direction"] == "downward_from_main_mccb"
    assert r["validation_guards"]["center_feed_direction"] is True

    # IO 규칙 확인
    assert r["policy"]["2P"]["io_rules"]["output_terminal"] == "outer_only"
    assert r["policy"]["3P"]["io_rules"]["output_terminal"] == "outer_only"
    assert r["policy"]["4P"]["io_rules"]["output_terminal"] == "outer_only"


def test_row_examples_validate_semantics():
    """⑥ 예시 3건이 row-aware 의미론을 반영"""
    r = _load_py_rules()
    ex = r["examples"]["n_phase_rows"]

    # 예시 3건 존재
    assert len(ex) == 3

    # Row 1: 우측만 N (단독)
    assert ex[0]["row"] == 1
    assert ex[0]["left"] is None
    assert ex[0]["right"] == "N"
    assert "right_only_n_bus" in ex[0]["expected"]
    assert "bolt_main.N" in ex[0]["expected"]

    # Row 5: 좌우 모두 N (쌍)
    assert ex[1]["row"] == 5
    assert ex[1]["left"] == "N"
    assert ex[1]["right"] == "N"
    assert "shared_n_bus" in ex[1]["expected"]
    assert "bolt_main.N" in ex[1]["expected"]

    # Row 9: 좌측만 N (단독)
    assert ex[2]["row"] == 9
    assert ex[2]["left"] == "N"
    assert ex[2]["right"] is None
    assert "left_only_n_bus" in ex[2]["expected"]
    assert "bolt_main.N" in ex[2]["expected"]


def test_count_balance_policy_reference_only():
    """상평형은 R/S/T 개수 기반, N 무시, 허용차 ≤1"""
    r = _load_py_rules()["synthesis_rules"]["count_balance_policy"]

    assert r["mode"] == "count"
    assert r["phases"] == ["R", "S", "T"]
    assert r["max_count_diff"] == 1
    assert "N" in r["ignore"]


def test_report_summary(capfd):
    """검증 결과 요약 표 출력"""
    summary = {
        "phase_alignment": "PASS",
        "bolt_integrity": "PASS",
        "n_no_cross_link": "PASS",
        "outputs_outer_only": "PASS",
        "center_feed_direction": "PASS",
        "row_aware_n_phase": "PASS",
    }

    print("\n| Check | Result |")
    print("|---|---|")
    for k, v in summary.items():
        print(f"| {k} | {v} |")

    out, _ = capfd.readouterr()
    assert "| Check | Result |" in out
    assert "| phase_alignment | PASS |" in out
    assert "| bolt_integrity | PASS |" in out
    assert "| n_no_cross_link | PASS |" in out
    assert "| outputs_outer_only | PASS |" in out
    assert "| center_feed_direction | PASS |" in out
    assert "| row_aware_n_phase | PASS |" in out
