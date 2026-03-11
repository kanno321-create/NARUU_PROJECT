"""
Unit Tests for Doc Lint Guard (Stage 5)
"""

from pathlib import Path
from kis_estimator_core.engine.doc_lint_guard import DocLintGuard
from kis_estimator_core.engine.models import ValidationReport


class TestDocLintGuard:
    """Doc Lint Guard 유닛 테스트"""

    def test_validate_with_missing_file(self):
        """파일 없을 때 오류 처리"""
        guard = DocLintGuard()
        validator_report = ValidationReport(
            formula_preservation=True,
            cross_references_valid=True,
            merged_cells_intact=True,
        )

        result = guard.validate(
            excel_path=Path("nonexistent.xlsx"),
            validator_report=validator_report,
        )

        assert result["passed"] is False
        assert result["score"] == 0.0
        assert len(result["errors"]) > 0

    def test_validate_with_formula_errors(self):
        """수식 보존 실패 시 오류"""
        guard = DocLintGuard()
        validator_report = ValidationReport(
            formula_preservation=False,  # 수식 보존 실패
            cross_references_valid=True,
            merged_cells_intact=True,
            violations=["수식 손상"],
        )

        # 실제 파일이 없어도 validator 결과만으로 체크 가능
        result = guard.validate(
            excel_path=Path("test.xlsx"),  # 존재하지 않음
            validator_report=validator_report,
        )

        assert result["passed"] is False
        assert result["checks"]["formula_preservation"] is False
        assert any("수식 보존 실패" in e for e in result["errors"])

    def test_validate_with_cross_reference_errors(self):
        """크로스 참조 실패 시 오류"""
        guard = DocLintGuard()
        validator_report = ValidationReport(
            formula_preservation=True,
            cross_references_valid=False,  # 크로스 참조 실패
            merged_cells_intact=True,
            violations=["크로스 참조 오류"],
        )

        result = guard.validate(
            excel_path=Path("test.xlsx"),
            validator_report=validator_report,
        )

        assert result["passed"] is False
        assert result["checks"]["cross_reference"] is False
        assert any("크로스 참조 오류" in e for e in result["errors"])

    def test_required_items_list(self):
        """필수 자재 12개 리스트 확인"""
        guard = DocLintGuard()

        # 필수 자재 12개
        expected_items = [
            "E.T",
            "N.T",
            "N.P",
            "MAIN BUS-BAR",
            "BUS-BAR",
            "COATING",
            "P-COVER",
            "차단기지지대",
            "ELB지지대",
            "INSULATOR",
            "잡자재비",
            "ASSEMBLY CHARGE",
        ]

        assert guard.REQUIRED_ITEMS == expected_items
