"""
실제 견적 작성 테스트

시나리오:
- 외함: 옥내노출 steel
- 메인차단기: 4P 200A
- 분기차단기:
  * MCCB 4P 75A × 2개
  * ELB 4P 40A × 4개
  * ELB 2P 50A × 2개
  * ELB 2P 20A × 14개
- 총 차단기: 메인 1개 + 분기 22개 = 23개
"""

import os
import pytest
from pathlib import Path

# CI skip - requires real template file (절대코어파일/견적서양식.xlsx)
pytestmark = pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipping real estimate tests in CI - requires real template file"
)
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver
from kis_estimator_core.engine.breaker_placer import BreakerPlacer
from kis_estimator_core.engine.breaker_critic import BreakerCritic
from kis_estimator_core.engine.data_transformer import DataTransformer
from kis_estimator_core.engine.excel_generator import ExcelGenerator
from kis_estimator_core.engine.doc_lint_guard import DocLintGuard
from kis_estimator_core.models.enclosure import (
    BreakerSpec,
    CustomerRequirements,
)


class TestRealEstimate:
    """실제 견적 작성 통합 테스트"""

    @pytest.fixture
    def template_path(self):
        """템플릿 경로"""
        return Path("절대코어파일/견적서양식.xlsx")

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """임시 출력 디렉토리"""
        output_dir = tmp_path / "real_estimate_output"
        output_dir.mkdir(exist_ok=True)
        return output_dir

    def test_real_estimate_case1(self, template_path, temp_output_dir):
        """
        실제 견적 케이스 1

        견적 내용:
        - 메인: 4P 200A
        - 분기: MCCB 4P 75A × 2, ELB 4P 40A × 4, ELB 2P 50A × 2, ELB 2P 20A × 14
        - 총 23개 차단기
        """
        print("\n" + "=" * 80)
        print("실제 견적 작성 테스트")
        print("=" * 80)

        # ==================== Stage 1: Enclosure ====================
        solver = EnclosureSolver()

        # 메인차단기: 4P 200A
        main_breaker = BreakerSpec(
            id="MAIN",
            model="SBS-203",  # 상도 표준형 4P 200AF (200A는 200AF)
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
                    model="SBE-104",  # 상도 경제형 4P 100AF 75A
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
                    model="SEE-54",  # 상도 누전 경제형 4P 50AF 40A
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
                    model="SEE-102",  # 상도 누전 경제형 2P 100AF 50A
                    poles=2,
                    current_a=50,
                    frame_af=100,
                )
            )

        # ELB 2P 20A × 14개 (소형 대신 50AF 사용)
        for i in range(14):
            branch_breakers.append(
                BreakerSpec(
                    id=f"ELB_2P_20A_{i+1}",
                    model="SEE-52",  # 상도 누전 경제형 2P 50AF 20A
                    poles=2,
                    current_a=20,
                    frame_af=50,  # 50AF 사용
                )
            )

        print(
            f"\n[입력] 메인차단기: {main_breaker.model} {main_breaker.poles}P {main_breaker.current_a}A"
        )
        print(f"[입력] 분기차단기: 총 {len(branch_breakers)}개")
        print("  - MCCB 4P 75A: 2개")
        print("  - ELB 4P 40A: 4개")
        print("  - ELB 2P 50A: 2개")
        print("  - ELB 2P 20A: 14개")

        # Stage 1 실행
        customer_reqs = CustomerRequirements(
            enclosure_type="옥내노출",
            material="steel",
            ip_rating="IP44",
        )

        enclosure_result = solver.solve(
            main_breaker=main_breaker,
            branch_breakers=branch_breakers,
            accessories=[],  # 부속자재는 나중에 계산
            customer_requirements=customer_reqs,
        )

        assert enclosure_result is not None
        dimensions = enclosure_result.dimensions
        print(
            f"\n[OK] Stage 1: 외함 크기 = {dimensions.width_mm}×{dimensions.height_mm}×{dimensions.depth_mm} mm"
        )

        # ==================== Stage 2: Breaker Placement ====================
        placer = BreakerPlacer()
        placement_result = placer.place(
            enclosure_result=enclosure_result,
            main_breaker=main_breaker,
            branch_breakers=branch_breakers,
        )

        assert placement_result is not None
        assert len(placement_result.placements) > 0
        print(
            f"[OK] Stage 2: 배치 완료 ({len(placement_result.placements)}개), 상평형 = {placement_result.phase_imbalance_pct:.1f}%"
        )

        # ==================== Stage 2.1: Critic ====================
        critic = BreakerCritic()
        critic_result = critic.evaluate(placement_result)

        assert critic_result is not None
        print(
            f"[OK] Stage 2.1: Critic 점수 = {critic_result.score}, 위반 = {critic_result.violations_count}"
        )

        # ==================== Stage 3: Data Transformation + Excel Generation ====================
        transformer = DataTransformer()
        estimate_data = transformer.transform(
            enclosure_result=enclosure_result,
            placement_result=placement_result,
            customer_name="실제 견적 테스트 고객",
            project_name="대표님 요청 견적",
        )

        assert estimate_data is not None
        assert len(estimate_data.panels) > 0
        print(
            f"[OK] Data Transformation: {len(estimate_data.panels[0].all_items_sorted)} 항목"
        )

        # Excel 생성
        generator = ExcelGenerator(template_path=template_path)
        estimate_output = generator.generate(
            estimate_data=estimate_data,
            customer_name="실제 견적 테스트 고객",
            project_name="대표님 요청 견적",
            output_dir=temp_output_dir,
            generate_pdf=False,
        )

        assert estimate_output is not None
        assert estimate_output.excel_path is not None
        assert estimate_output.excel_path.exists()
        print(f"[OK] Stage 3: Excel 생성 = {estimate_output.excel_path}")

        # ==================== Stage 5: Doc Lint ====================
        guard = DocLintGuard()
        lint_result = guard.validate(
            excel_path=estimate_output.excel_path,
            validator_report=estimate_output.validation_report,
        )

        assert lint_result["passed"] is True
        assert lint_result["score"] >= 0.8
        print(
            f"[OK] Stage 5: Lint 통과 = {lint_result['passed']}, 점수 = {lint_result['score']:.2f}"
        )

        # ==================== 결과 출력 ====================
        print("\n" + "=" * 80)
        print("견적서 생성 완료")
        print("=" * 80)
        print(f"파일 경로: {estimate_output.excel_path}")
        print(
            f"외함: {dimensions.width_mm}×{dimensions.height_mm}×{dimensions.depth_mm} mm"
        )
        print(f"총 항목: {len(estimate_data.panels[0].all_items_sorted)}개")
        print(f"품질 점수: {lint_result['score']:.2f}")
        print("=" * 80)

        # Excel 파일 자동 열기
        import subprocess

        subprocess.run(
            ["start", str(estimate_output.excel_path)], shell=True, check=False
        )
