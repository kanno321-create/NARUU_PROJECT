"""
Test enclosure_solver.py - __init__ method
Phase I-5 Wave 8b (1/6)

Zero-Mock 준수: 실제 지식파일 (temp_basic_knowledge/core_rules.json) 사용
"""

import pytest
from pathlib import Path
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver
from kis_estimator_core.core.ssot.errors import EstimatorError


class TestEnclosureSolverInit:
    """__init__ 메서드 테스트"""

    def test_init_default_path(self):
        """기본 경로로 초기화 (temp_basic_knowledge/core_rules.json)."""
        solver = EnclosureSolver()

        assert solver.knowledge is not None
        assert isinstance(solver.knowledge, dict)

        # 필수 섹션 존재 확인
        assert "breaker_dimensions_mm" in solver.knowledge
        assert "frame_clearances" in solver.knowledge
        assert "enclosure_width_rules_mm" in solver.knowledge
        assert "depth_rules_mm" in solver.knowledge

    def test_init_custom_path(self):
        """커스텀 경로로 초기화."""
        # 기본 경로 사용 (temp_basic_knowledge/core_rules.json)
        knowledge_path = (
            Path(__file__).parent.parent.parent.parent
            / "temp_basic_knowledge"
            / "core_rules.json"
        )

        solver = EnclosureSolver(knowledge_path=knowledge_path)
        assert solver.knowledge is not None
        assert isinstance(solver.knowledge, dict)

    def test_init_missing_file(self):
        """지식파일이 없을 때 오류 발생."""
        fake_path = Path("/nonexistent/core_rules.json")

        with pytest.raises(EstimatorError) as exc_info:
            EnclosureSolver(knowledge_path=fake_path)

        assert "지식파일을 찾을 수 없습니다" in str(exc_info.value)
        assert "목업 데이터는 사용하지 않습니다" in str(exc_info.value)

    def test_init_incomplete_knowledge(self, tmp_path):
        """필수 섹션이 없는 지식파일일 때 오류 발생."""
        # 불완전한 지식파일 생성
        incomplete_file = tmp_path / "incomplete.json"
        incomplete_file.write_text('{"breaker_dimensions_mm": {}}', encoding="utf-8")

        with pytest.raises(EstimatorError) as exc_info:
            EnclosureSolver(knowledge_path=incomplete_file)

        assert "필수 섹션이 없습니다" in str(exc_info.value)

    def test_init_knowledge_structure(self):
        """지식파일 구조 검증 (breaker_dimensions_mm)."""
        solver = EnclosureSolver()

        dims = solver.knowledge["breaker_dimensions_mm"]
        assert "small_32" in dims  # 소형 차단기
        assert "FB" in dims  # FB 타입
        assert "50AF_econ_std" in dims  # 50AF
        assert "100AF_econ" in dims  # 100AF 경제형

    def test_init_frame_clearances_structure(self):
        """지식파일 구조 검증 (frame_clearances)."""
        solver = EnclosureSolver()

        clearances = solver.knowledge["frame_clearances"]
        assert "rules" in clearances
        assert isinstance(clearances["rules"], list)
        assert len(clearances["rules"]) > 0

        # 첫 번째 규칙 확인
        first_rule = clearances["rules"][0]
        assert "top" in first_rule
        assert "bottom" in first_rule

    def test_init_width_rules_structure(self):
        """지식파일 구조 검증 (enclosure_width_rules_mm)."""
        solver = EnclosureSolver()

        width_rules = solver.knowledge["enclosure_width_rules_mm"]
        assert "rules" in width_rules
        assert isinstance(width_rules["rules"], list)
        assert len(width_rules["rules"]) > 0

    def test_init_depth_rules_structure(self):
        """지식파일 구조 검증 (depth_rules_mm)."""
        solver = EnclosureSolver()

        depth_rules = solver.knowledge["depth_rules_mm"]
        # depth_rules 구조는 간단함 (PBL 유무로 결정)
        assert depth_rules is not None
