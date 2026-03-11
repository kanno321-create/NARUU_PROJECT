#!/usr/bin/env python3
"""
실제 견적 생성 스크립트

사용법:
python scripts/generate_estimate.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.kis_estimator_core.engine.enclosure_solver import EnclosureSolver
from src.kis_estimator_core.models.enclosure import (
    BreakerSpec,
    CustomerRequirements,
)
from src.kis_estimator_core.engine.breaker_placer import BreakerPlacer, BreakerInput, PanelSpec
from src.kis_estimator_core.engine.estimate_formatter import EstimateFormatter
from src.kis_estimator_core.engine.doc_lint_guard import DocLintGuard


def main():
    print("=" * 80)
    print("실제 견적 생성")
    print("=" * 80)

    # ==================== 견적 사양 ====================
    print("\n[견적 사양]")
    print("- 외함: 옥내노출 steel")
    print("- 메인차단기: 4P 200A")
    print("- 분기차단기:")
    print("  * MCCB 4P 75A × 2개")
    print("  * ELB 4P 40A × 4개")
    print("  * ELB 2P 50A × 2개")
    print("  * ELB 2P 20A × 14개")

    # ==================== Stage 1: Enclosure ====================
    solver = EnclosureSolver()

    # 메인차단기: 4P 200A
    main_breaker = BreakerSpec(
        id="MAIN",
        model="SBS-203",
        poles=4,
        current_a=200,
        frame_af=200,
    )

    # 분기차단기
    branch_breakers = []

    # MCCB 4P 75A × 2개
    for i in range(2):
        branch_breakers.append(
            BreakerSpec(
                id=f"MCCB_4P_75A_{i+1}",
                model="SBE-104",
                poles=4,
                current_a=75,
                frame_af=100,
            )
        )

    # ELB 4P 40A × 4개
    for i in range(4):
        branch_breakers.append(
            BreakerSpec(
                id=f"ELB_4P_40A_{i+1}",
                model="SEE-54",
                poles=4,
                current_a=40,
                frame_af=50,
            )
        )

    # ELB 2P 50A × 2개
    for i in range(2):
        branch_breakers.append(
            BreakerSpec(
                id=f"ELB_2P_50A_{i+1}",
                model="SEE-102",
                poles=2,
                current_a=50,
                frame_af=100,
            )
        )

    # ELB 2P 20A × 14개
    for i in range(14):
        branch_breakers.append(
            BreakerSpec(
                id=f"ELB_2P_20A_{i+1}",
                model="SEE-52",
                poles=2,
                current_a=20,
                frame_af=50,
            )
        )

    # Stage 1 실행
    customer_reqs = CustomerRequirements(
        enclosure_type="옥내노출",
        material="steel",
        ip_rating="IP44",
    )

    enclosure_result = solver.solve(
        main_breaker=main_breaker,
        branch_breakers=branch_breakers,
        accessories=[],
        customer_requirements=customer_reqs,
    )

    dimensions = enclosure_result.dimensions
    print(f"\n[Stage 1] 외함 크기: {dimensions.width_mm}×{dimensions.height_mm}×{dimensions.depth_mm} mm")

    # ==================== Stage 2: Breaker Placement ====================
    # BreakerPlacer는 치수 정보가 필요 - 간단하게 더미 치수 사용
    placer = BreakerPlacer()

    # 차단기 정보를 BreakerInput 형식으로 변환
    breaker_inputs = []

    # 메인 차단기 (간단 치수)
    breaker_inputs.append(
        BreakerInput(
            id=main_breaker.id,
            poles=main_breaker.poles,
            current_a=main_breaker.current_a,
            width_mm=140,  # 4P 200AF 예상 치수
            height_mm=165,
            depth_mm=60,
            breaker_type="normal"
        )
    )

    # 분기 차단기
    for b in branch_breakers:
        if b.frame_af == 100:
            w, h, d = (50, 130, 60) if b.poles == 2 else (100, 130, 60)  # 100AF
        elif b.frame_af == 50:
            w, h, d = (50, 130, 60) if b.poles == 2 else (100, 130, 60)  # 50AF
        else:
            w, h, d = (50, 130, 60) if b.poles == 2 else (100, 130, 60)  # 기본값

        breaker_inputs.append(
            BreakerInput(
                id=b.id,
                poles=b.poles,
                current_a=b.current_a,
                width_mm=w,
                height_mm=h,
                depth_mm=d,
                breaker_type="normal"
            )
        )

    panel_spec = PanelSpec(
        width_mm=dimensions.width_mm,
        height_mm=dimensions.height_mm,
        depth_mm=dimensions.depth_mm,
        clearance_mm=50,  # 기본 간격
    )

    placements = placer.place(breakers=breaker_inputs, panel=panel_spec)
    print(f"[Stage 2] 배치 완료: {len(placements)}개")

    # ==================== Stage 3: EstimateFormatter ====================
    template_path = project_root / "절대코어파일" / "견적서양식.xlsx"
    output_dir = project_root / "outputs"
    output_dir.mkdir(exist_ok=True)

    formatter = EstimateFormatter(template_path=template_path)
    estimate_output = formatter.format(
        enclosure_result=enclosure_result,
        placements=placements,
        breakers=breaker_inputs,
        customer_name="대표님",
        project_name="실제 견적 작성 테스트",
        output_dir=output_dir,
        generate_pdf=False,
    )

    print(f"[Stage 3] 견적서 생성: {estimate_output.excel_path}")

    # ==================== Stage 5: Doc Lint ====================
    guard = DocLintGuard()
    lint_result = guard.validate(
        excel_path=estimate_output.excel_path,
        validator_report=estimate_output.validation_report,
    )

    print(f"[Stage 5] Lint 검증: {lint_result['passed']}, 점수: {lint_result['score']:.2f}")

    # ==================== 결과 ====================
    print("\n" + "=" * 80)
    print("견적서 생성 완료!")
    print("=" * 80)
    print(f"파일: {estimate_output.excel_path}")
    print(f"외함: {dimensions.width_mm}×{dimensions.height_mm}×{dimensions.depth_mm} mm")
    print(f"품질: {lint_result['score']:.2f}")
    print("=" * 80)

    # Excel 파일 열기
    import subprocess

    subprocess.run(["start", str(estimate_output.excel_path)], shell=True, check=False)


if __name__ == "__main__":
    main()
