"""
실제 견적 테스트 - 11개 케이스 (NO MOCKS)

대표님 요청:
- 옥내노출 스틸 1.6T
- 상도차단기, 경제형
- 메인 4P 50A
- 분기 ELB 4P 20A 2개
- 분기 ELB 2P 20A 10개

+ 유사 견적 10개 추가
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from kis_estimator_core.engine.workflow_engine import WorkflowEngine
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver
from kis_estimator_core.engine.data_transformer import DataTransformer
from kis_estimator_core.engine.breaker_placer import BreakerPlacer, BreakerInput, PanelSpec
from kis_estimator_core.models.enclosure import BreakerSpec, AccessorySpec, CustomerRequirements


# 테스트 케이스 정의 (11개)
TEST_CASES = [
    # 케이스 1: 대표님 원본 요청 (32AF → 50AF로 매핑, 소형 차단기는 외함 계산시 50AF 규칙 적용)
    {
        "name": "케이스1_원본요청",
        "enclosure_type": "옥내노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "상도",
        "main_breaker": {"poles": 4, "current": 50, "frame_af": 50, "model": "SBE-54"},
        "branch_breakers": [
            {"poles": 4, "current": 20, "frame_af": 50, "quantity": 2, "model": "SEE-54", "breaker_type": "ELB"},
            {"poles": 2, "current": 20, "frame_af": 30, "quantity": 10, "model": "SIE-32", "breaker_type": "ELB"},
        ],
        "accessories": [],
    },
    # 케이스 2: 메인 100AF, 분기 증가
    {
        "name": "케이스2_메인100AF",
        "enclosure_type": "옥내노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "상도",
        "main_breaker": {"poles": 4, "current": 75, "frame_af": 100, "model": "SBE-104"},
        "branch_breakers": [
            {"poles": 4, "current": 30, "frame_af": 50, "quantity": 4, "model": "SEE-54", "breaker_type": "ELB"},
            {"poles": 2, "current": 20, "frame_af": 30, "quantity": 12, "model": "SIE-32", "breaker_type": "ELB"},
        ],
        "accessories": [],
    },
    # 케이스 3: 메인 200AF, 대형 분전반
    {
        "name": "케이스3_메인200AF",
        "enclosure_type": "옥내노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "상도",
        "main_breaker": {"poles": 4, "current": 150, "frame_af": 200, "model": "SBE-204"},
        "branch_breakers": [
            {"poles": 4, "current": 50, "frame_af": 50, "quantity": 4, "model": "SBE-54", "breaker_type": "MCCB"},
            {"poles": 3, "current": 30, "frame_af": 50, "quantity": 6, "model": "SEE-53", "breaker_type": "ELB"},
            {"poles": 2, "current": 20, "frame_af": 30, "quantity": 8, "model": "SIE-32", "breaker_type": "ELB"},
        ],
        "accessories": [],
    },
    # 케이스 4: 마그네트 포함
    {
        "name": "케이스4_마그네트포함",
        "enclosure_type": "옥내노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "상도",
        "main_breaker": {"poles": 4, "current": 75, "frame_af": 100, "model": "SBE-104"},
        "branch_breakers": [
            {"poles": 4, "current": 30, "frame_af": 50, "quantity": 3, "model": "SEE-54", "breaker_type": "ELB"},
            {"poles": 2, "current": 20, "frame_af": 30, "quantity": 6, "model": "SIE-32", "breaker_type": "ELB"},
        ],
        "accessories": [
            {"type": "magnet", "model": "MC-22", "quantity": 2},
        ],
    },
    # 케이스 5: 옥외노출
    {
        "name": "케이스5_옥외노출",
        "enclosure_type": "옥외노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "상도",
        "main_breaker": {"poles": 4, "current": 60, "frame_af": 100, "model": "SBE-104"},
        "branch_breakers": [
            {"poles": 4, "current": 30, "frame_af": 50, "quantity": 3, "model": "SEE-54", "breaker_type": "ELB"},
            {"poles": 2, "current": 20, "frame_af": 30, "quantity": 8, "model": "SIE-32", "breaker_type": "ELB"},
        ],
        "accessories": [],
    },
    # 케이스 6: 3P 메인
    {
        "name": "케이스6_3P메인",
        "enclosure_type": "옥내노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "상도",
        "main_breaker": {"poles": 3, "current": 75, "frame_af": 100, "model": "SBE-103"},
        "branch_breakers": [
            {"poles": 3, "current": 30, "frame_af": 50, "quantity": 5, "model": "SEE-53", "breaker_type": "ELB"},
            {"poles": 3, "current": 20, "frame_af": 50, "quantity": 4, "model": "SBE-53", "breaker_type": "MCCB"},
        ],
        "accessories": [],
    },
    # 케이스 7: 소형 분전반 (50AF 사용 - 32AF는 소형 전용, 외함 계산에서 50AF 규칙 사용)
    {
        "name": "케이스7_소형분전반",
        "enclosure_type": "옥내노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "상도",
        "main_breaker": {"poles": 2, "current": 30, "frame_af": 50, "model": "SBE-52"},
        "branch_breakers": [
            {"poles": 2, "current": 20, "frame_af": 30, "quantity": 4, "model": "SIE-32", "breaker_type": "ELB"},
        ],
        "accessories": [],
    },
    # 케이스 8: 400AF 대용량
    {
        "name": "케이스8_400AF대용량",
        "enclosure_type": "옥내노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "상도",
        "main_breaker": {"poles": 4, "current": 300, "frame_af": 400, "model": "SBS-404"},
        "branch_breakers": [
            {"poles": 4, "current": 100, "frame_af": 100, "quantity": 4, "model": "SBE-104", "breaker_type": "MCCB"},
            {"poles": 4, "current": 50, "frame_af": 50, "quantity": 6, "model": "SEE-54", "breaker_type": "ELB"},
        ],
        "accessories": [],
    },
    # 케이스 9: 타이머 포함
    {
        "name": "케이스9_타이머포함",
        "enclosure_type": "옥내노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "상도",
        "main_breaker": {"poles": 4, "current": 75, "frame_af": 100, "model": "SBE-104"},
        "branch_breakers": [
            {"poles": 4, "current": 30, "frame_af": 50, "quantity": 2, "model": "SEE-54", "breaker_type": "ELB"},
            {"poles": 2, "current": 20, "frame_af": 30, "quantity": 6, "model": "SIE-32", "breaker_type": "ELB"},
        ],
        "accessories": [
            {"type": "timer", "model": "24H", "quantity": 1},
        ],
    },
    # 케이스 10: LS 브랜드
    {
        "name": "케이스10_LS브랜드",
        "enclosure_type": "옥내노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "LS",
        "main_breaker": {"poles": 4, "current": 75, "frame_af": 100, "model": "ABN-104"},
        "branch_breakers": [
            {"poles": 4, "current": 30, "frame_af": 50, "quantity": 3, "model": "EBN-54", "breaker_type": "ELB"},
            {"poles": 2, "current": 20, "frame_af": 30, "quantity": 8, "model": "32GRHS", "breaker_type": "ELB"},
        ],
        "accessories": [],
    },
    # 케이스 11: 복합 (마그네트+타이머+다양한 분기)
    {
        "name": "케이스11_복합구성",
        "enclosure_type": "옥내노출",
        "material": "STEEL 1.6T",
        "breaker_brand": "상도",
        "main_breaker": {"poles": 4, "current": 100, "frame_af": 125, "model": "SBS-124"},
        "branch_breakers": [
            {"poles": 4, "current": 50, "frame_af": 50, "quantity": 2, "model": "SBE-54", "breaker_type": "MCCB"},
            {"poles": 4, "current": 30, "frame_af": 50, "quantity": 3, "model": "SEE-54", "breaker_type": "ELB"},
            {"poles": 3, "current": 30, "frame_af": 50, "quantity": 2, "model": "SEE-53", "breaker_type": "ELB"},
            {"poles": 2, "current": 20, "frame_af": 30, "quantity": 8, "model": "SIE-32", "breaker_type": "ELB"},
        ],
        "accessories": [
            {"type": "magnet", "model": "MC-22", "quantity": 1},
            {"type": "timer", "model": "24H", "quantity": 1},
        ],
    },
]


_breaker_counter = 0

def create_breaker_spec(data: dict, prefix: str = "BR") -> BreakerSpec:
    """딕셔너리 → BreakerSpec 변환"""
    global _breaker_counter
    _breaker_counter += 1
    return BreakerSpec(
        id=f"{prefix}-{_breaker_counter:04d}",
        model=data.get("model", "AUTO"),
        poles=data["poles"],
        current_a=data["current"],
        frame_af=data["frame_af"],
    )


def create_accessory_spec(data: dict) -> AccessorySpec:
    """딕셔너리 → AccessorySpec 변환"""
    return AccessorySpec(
        type=data["type"],
        model=data.get("model", ""),
        quantity=data.get("quantity", 1),
    )


# 차단기 치수 테이블 (CLAUDE.md 참조)
BREAKER_DIMENSIONS = {
    # (frame_af, poles): (width, height, depth)
    (32, 2): (33, 70, 42),    # 소형 2P
    (50, 2): (50, 130, 60),
    (50, 3): (75, 130, 60),
    (50, 4): (100, 130, 60),
    (100, 2): (50, 130, 60),   # 경제형
    (100, 3): (75, 130, 60),
    (100, 4): (100, 130, 60),
    (125, 2): (60, 155, 60),   # 표준형
    (125, 3): (90, 155, 60),
    (125, 4): (120, 155, 60),
    (200, 2): (70, 165, 60),
    (200, 3): (105, 165, 60),
    (200, 4): (140, 165, 60),
    (250, 2): (70, 165, 60),
    (250, 3): (105, 165, 60),
    (250, 4): (140, 165, 60),
    (400, 3): (140, 257, 109),
    (400, 4): (187, 257, 109),
    (600, 3): (210, 280, 109),
    (600, 4): (280, 280, 109),
    (800, 3): (210, 280, 109),
    (800, 4): (280, 280, 109),
}


_placement_counter = 0


def create_breaker_input(data: dict, prefix: str = "BR") -> BreakerInput:
    """딕셔너리 → BreakerInput 변환 (배치용)"""
    global _placement_counter
    _placement_counter += 1

    af = data["frame_af"]
    poles = data["poles"]

    # 치수 조회 (기본값: 50AF 기준)
    dims = BREAKER_DIMENSIONS.get((af, poles), BREAKER_DIMENSIONS.get((50, poles), (100, 130, 60)))

    return BreakerInput(
        id=f"{prefix}-{_placement_counter:04d}",
        poles=poles,
        current_a=data["current"],
        width_mm=dims[0],
        height_mm=dims[1],
        depth_mm=dims[2],
        model=data.get("model", "AUTO"),
        breaker_type="small" if af == 32 else "normal",
    )


async def run_enclosure_test(case: dict) -> dict:
    """외함 계산 테스트"""
    try:
        solver = EnclosureSolver()

        main_breaker = create_breaker_spec(case["main_breaker"], prefix="MAIN")

        # 분기 차단기 확장 (quantity 반영)
        branch_breakers = []
        for bb_data in case["branch_breakers"]:
            qty = bb_data.get("quantity", 1)
            for _ in range(qty):
                branch_breakers.append(create_breaker_spec(bb_data, prefix="BR"))

        accessories = [create_accessory_spec(acc) for acc in case.get("accessories", [])]

        # 높이 계산
        H_total, H_breakdown = solver.calculate_height(main_breaker, branch_breakers, accessories)

        # 폭 계산
        W_total, W_breakdown = solver.calculate_width(main_breaker, branch_breakers)

        # 깊이 계산
        D_total, D_breakdown = solver.calculate_depth(accessories)

        return {
            "success": True,
            "dimensions": {
                "W": W_total,
                "H": H_total,
                "D": D_total,
            },
            "breakdown": {
                "H_breakdown": H_breakdown,
                "W_breakdown": W_breakdown,
                "D_breakdown": D_breakdown,
            },
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def run_placement_test(case: dict, enclosure_dims: dict) -> dict:
    """분기차단기 배치 테스트"""
    global _placement_counter
    _placement_counter = 0

    try:
        placer = BreakerPlacer()

        # 메인 차단기
        main_input = create_breaker_input(case["main_breaker"], prefix="MAIN")

        # 분기 차단기 확장 (quantity 반영)
        breakers = [main_input]
        for bb_data in case["branch_breakers"]:
            qty = bb_data.get("quantity", 1)
            for _ in range(qty):
                breakers.append(create_breaker_input(bb_data, prefix="BR"))

        # 패널 스펙 (외함 계산 결과 사용)
        panel = PanelSpec(
            width_mm=int(enclosure_dims.get("W", 600)),
            height_mm=int(enclosure_dims.get("H", 1200)),
            depth_mm=int(enclosure_dims.get("D", 150)),
            clearance_mm=50,
        )

        # 배치 실행
        placements = placer.place(breakers, panel)

        # 검증 실행
        validation = placer.validate(placements)

        # 상평형 통계
        phase_counts = {"R": 0, "S": 0, "T": 0}
        for p in placements:
            if p.position.get("row") == 0 or p.poles >= 3:
                continue
            phase = p.phase
            if phase in phase_counts:
                phase_counts[phase] += 1

        return {
            "success": validation.is_valid,
            "total_placements": len(placements),
            "phase_counts": phase_counts,
            "phase_imbalance": validation.phase_imbalance_pct,
            "clearance_violations": validation.clearance_violations,
            "errors": validation.errors,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def run_workflow_test(case: dict) -> dict:
    """전체 워크플로우 테스트 (실제 견적 생성)"""
    try:
        engine = WorkflowEngine()

        result = await engine.execute(
            enclosure_type=case["enclosure_type"],
            enclosure_material=case["material"],
            breaker_brand=case["breaker_brand"],
            main_breaker=case["main_breaker"],
            branch_breakers=case["branch_breakers"],
            accessories=case.get("accessories", []),
            customer_name="테스트고객",
            project_name=case["name"],
        )

        return {
            "success": result.success,
            "phases": len(result.phases),
            "blocking_errors": len(result.blocking_errors) if result.blocking_errors else 0,
            "final_output": str(result.final_output) if result.final_output else None,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def run_all_tests():
    """모든 테스트 실행"""
    global _breaker_counter
    print("=" * 80)
    print("실제 견적 테스트 시작 - 11개 케이스 (NO MOCKS)")
    print("=" * 80)

    results = []

    for i, case in enumerate(TEST_CASES, 1):
        # 각 케이스마다 카운터 리셋
        _breaker_counter = 0
        print(f"\n[{i}/11] {case['name']} 테스트 중...")
        print(f"  메인: {case['main_breaker']['poles']}P {case['main_breaker']['current']}A ({case['main_breaker']['frame_af']}AF)")

        total_branch = sum(bb.get("quantity", 1) for bb in case["branch_breakers"])
        print(f"  분기: 총 {total_branch}개")

        for bb in case["branch_breakers"]:
            print(f"    - {bb.get('breaker_type', 'MCCB')} {bb['poles']}P {bb['current']}A x{bb.get('quantity', 1)}")

        if case.get("accessories"):
            print(f"  부속: {len(case['accessories'])}종")
            for acc in case["accessories"]:
                print(f"    - {acc['type']} {acc.get('model', '')} x{acc.get('quantity', 1)}")

        # 외함 계산 테스트
        enclosure_result = await run_enclosure_test(case)

        if enclosure_result["success"]:
            dims = enclosure_result["dimensions"]
            print(f"  외함 계산 성공: {dims['W']}×{dims['H']}×{dims['D']}mm")
        else:
            print(f"  외함 계산 실패: {enclosure_result.get('error', 'Unknown')}")

        # 분기차단기 배치 테스트 (외함 계산 성공 시에만)
        placement_result = {"success": False, "error": "외함 계산 실패로 배치 테스트 스킵"}
        if enclosure_result["success"]:
            placement_result = await run_placement_test(case, enclosure_result["dimensions"])
            if placement_result["success"]:
                print(f"  배치 성공: {placement_result['total_placements']}개 배치, 상평형={placement_result['phase_imbalance']:.1f}%, 간섭={placement_result['clearance_violations']}")
            else:
                print(f"  배치 실패: {placement_result.get('error', 'Unknown')}")

        # 전체 워크플로우 테스트
        workflow_result = await run_workflow_test(case)

        if workflow_result["success"]:
            print(f"  워크플로우 성공: {workflow_result['phases']}단계 완료")
            if workflow_result["final_output"]:
                print(f"  출력파일: {workflow_result['final_output']}")
        else:
            print(f"  워크플로우 실패: {workflow_result.get('error', 'Unknown')}")

        results.append({
            "case": case["name"],
            "enclosure": enclosure_result,
            "placement": placement_result,
            "workflow": workflow_result,
        })

    # 결과 요약
    print("\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)

    enclosure_success = sum(1 for r in results if r["enclosure"]["success"])
    placement_success = sum(1 for r in results if r["placement"]["success"])
    workflow_success = sum(1 for r in results if r["workflow"]["success"])

    print(f"\n외함 계산: {enclosure_success}/11 성공")
    print(f"배치 검증: {placement_success}/11 성공")
    print(f"워크플로우: {workflow_success}/11 성공")

    print("\n상세 결과:")
    print("-" * 100)
    print(f"{'케이스':<25} {'외함':<8} {'배치':<8} {'워크':<8} {'외함크기':<18} {'상평형':<10} {'간섭'}")
    print("-" * 100)

    for r in results:
        enc_status = "성공" if r["enclosure"]["success"] else "실패"
        pl_status = "성공" if r["placement"]["success"] else "실패"
        wf_status = "성공" if r["workflow"]["success"] else "실패"

        if r["enclosure"]["success"]:
            dims = r["enclosure"]["dimensions"]
            size = f"{int(dims['W'])}×{int(dims['H'])}×{int(dims['D'])}"
        else:
            size = "계산실패"

        if r["placement"]["success"]:
            phase_bal = f"{r['placement']['phase_imbalance']:.1f}%"
            clearance = str(r["placement"]["clearance_violations"])
        else:
            phase_bal = "-"
            clearance = "-"

        print(f"{r['case']:<25} {enc_status:<8} {pl_status:<8} {wf_status:<8} {size:<18} {phase_bal:<10} {clearance}")

    print("-" * 100)

    # 실패 케이스 상세
    failed_cases = [r for r in results if not r["enclosure"]["success"] or not r["placement"]["success"] or not r["workflow"]["success"]]
    if failed_cases:
        print("\n실패 케이스 상세:")
        for r in failed_cases:
            print(f"\n  {r['case']}:")
            if not r["enclosure"]["success"]:
                print(f"    외함: {r['enclosure'].get('error', 'Unknown')}")
            if not r["placement"]["success"]:
                print(f"    배치: {r['placement'].get('error', 'Unknown')}")
            if not r["workflow"]["success"]:
                print(f"    워크플로우: {r['workflow'].get('error', 'Unknown')}")

    return results


if __name__ == "__main__":
    results = asyncio.run(run_all_tests())
