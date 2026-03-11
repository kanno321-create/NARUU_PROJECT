"""
T4: enclosure_validator.py 커버리지 완성 (0% → 100%)

목표: validate_breaker_spec(), normalize_dimension_uom(), validate_dimension_range(), validate_enclosure_input() 전체 분기 커버

Zero-Mock 원칙:
- 실제 ValidationError 사용
- 실제 constants import
- 실제 데이터로 검증

일관성 규칙:
- error_code 체크: exc_info.value.error_code.code
- details 체크: exc_info.value.details
- (참조: tests/unit/test_error_integration.py)
"""

import pytest
from kis_estimator_core.validators.enclosure_validator import (
    validate_breaker_spec,
    normalize_dimension_uom,
    validate_dimension_range,
    validate_enclosure_input,
)
from kis_estimator_core.errors.exceptions import ValidationError


class TestValidateBreakerSpec:
    """validate_breaker_spec() 전체 분기 테스트"""

    def test_valid_2p_50af(self):
        """정상: 2P 50AF 차단기"""
        breaker = {"frame_af": 50, "poles": 2, "model": "SBE-52"}
        validate_breaker_spec(breaker)  # 예외 없음

    def test_valid_3p_100af(self):
        """정상: 3P 100AF 차단기"""
        breaker = {"frame_af": 100, "poles": 3, "model": "SBE-103"}
        validate_breaker_spec(breaker)  # 예외 없음

    def test_invalid_af_value(self):
        """오류: 잘못된 AF 값 (999)"""
        breaker = {"frame_af": 999, "poles": 2, "model": "INVALID"}
        with pytest.raises(ValidationError) as exc_info:
            validate_breaker_spec(breaker)
        # 일관성: error_code 및 details 체크
        assert exc_info.value.error_code.code == "ENC-003"
        assert exc_info.value.details.get("field") == "breaker.frame_af"

    def test_invalid_32af_3p(self):
        """오류: 32AF는 2P만 가능 (3P 불가)"""
        breaker = {"frame_af": 32, "poles": 3, "model": "SIE-32"}
        with pytest.raises(ValidationError) as exc_info:
            validate_breaker_spec(breaker)
        # 일관성: error_code 및 details 체크
        assert exc_info.value.error_code.code == "ENC-003"
        assert "허용 극수" in exc_info.value.details.get("expected", "")

    def test_invalid_400af_2p(self):
        """오류: 400AF는 3P/4P만 가능 (2P 불가)"""
        breaker = {"frame_af": 400, "poles": 2, "model": "SBE-402"}
        with pytest.raises(ValidationError) as exc_info:
            validate_breaker_spec(breaker)
        # 일관성: error_code 및 details 체크
        assert exc_info.value.error_code.code == "ENC-003"
        assert "허용 극수" in exc_info.value.details.get("expected", "")

    def test_invalid_general_pole_combination(self):
        """오류: 일반적인 AF-Pole 조합 위반"""
        breaker = {"frame_af": 100, "poles": 5, "model": "INVALID"}  # 5P는 없음
        with pytest.raises(ValidationError) as exc_info:
            validate_breaker_spec(breaker)
        # 일관성: error_code 및 details 체크
        assert exc_info.value.error_code.code == "ENC-003"
        assert "허용 극수" in exc_info.value.details.get("expected", "")


class TestNormalizeDimensionUom:
    """normalize_dimension_uom() 전체 분기 테스트"""

    def test_int_input(self):
        """정상: int 입력 (기본 mm)"""
        result = normalize_dimension_uom(100, "width")
        assert result == 100.0

    def test_float_input(self):
        """정상: float 입력 (기본 mm)"""
        result = normalize_dimension_uom(150.5, "height")
        assert result == 150.5

    def test_mm_string(self):
        """정상: "100mm" 문자열"""
        result = normalize_dimension_uom("100mm", "width")
        assert result == 100.0

    def test_cm_string(self):
        """정상: "10cm" 문자열 (10cm = 100mm)"""
        result = normalize_dimension_uom("10cm", "width")
        assert result == 100.0

    def test_inch_string(self):
        """정상: "5inch" 문자열 (5inch = 127mm)"""
        result = normalize_dimension_uom("5inch", "width")
        assert result == pytest.approx(127.0, rel=1e-2)

    def test_invalid_string(self):
        """오류: 파싱 불가능한 문자열"""
        with pytest.raises(ValidationError) as exc_info:
            normalize_dimension_uom("invalid", "width")
        # 일관성: error_code 및 details 체크
        assert exc_info.value.error_code.code == "ENC-003"
        assert "100mm" in exc_info.value.details.get("expected", "")

    def test_invalid_type_none(self):
        """오류: None 입력"""
        with pytest.raises(ValidationError) as exc_info:
            normalize_dimension_uom(None, "width")
        # 일관성: error_code 및 details 체크
        assert exc_info.value.error_code.code == "ENC-003"
        assert "100mm" in exc_info.value.details.get("expected", "")


class TestValidateDimensionRange:
    """validate_dimension_range() 전체 분기 테스트"""

    def test_within_range(self):
        """정상: 범위 내 값"""
        validate_dimension_range(500.0, "width", 100.0, 1000.0)  # 예외 없음

    def test_at_min_boundary(self):
        """정상: 최소값 경계"""
        validate_dimension_range(100.0, "width", 100.0, 1000.0)  # 예외 없음

    def test_at_max_boundary(self):
        """정상: 최대값 경계"""
        validate_dimension_range(1000.0, "width", 100.0, 1000.0)  # 예외 없음

    def test_below_min(self):
        """오류: 최소값 미만"""
        with pytest.raises(ValidationError) as exc_info:
            validate_dimension_range(50.0, "width", 100.0, 1000.0)
        # 일관성: error_code 및 details 체크
        assert exc_info.value.error_code.code == "ENC-003"
        assert "100.0" in exc_info.value.details.get("expected", "")
        assert "1000.0" in exc_info.value.details.get("expected", "")

    def test_above_max(self):
        """오류: 최대값 초과"""
        with pytest.raises(ValidationError) as exc_info:
            validate_dimension_range(1500.0, "width", 100.0, 1000.0)
        # 일관성: error_code 및 details 체크
        assert exc_info.value.error_code.code == "ENC-003"
        assert "범위" in exc_info.value.details.get("expected", "")


class TestValidateEnclosureInput:
    """validate_enclosure_input() 전체 분기 테스트"""

    def test_valid_single_panel(self):
        """정상: 메인 1개 + 분기 3개"""
        main = {"frame_af": 100, "poles": 3, "model": "SBE-103"}
        branches = [
            {"frame_af": 50, "poles": 2, "model": "SBE-52"},
            {"frame_af": 50, "poles": 2, "model": "SBE-52"},
            {"frame_af": 50, "poles": 2, "model": "SBE-52"},
        ]
        validate_enclosure_input(main, branches)  # 예외 없음

    def test_invalid_main_breaker(self):
        """오류: 메인 차단기 AF-Pole 위반"""
        main = {"frame_af": 32, "poles": 3, "model": "INVALID"}  # 32AF는 2P만
        branches = [{"frame_af": 50, "poles": 2, "model": "SBE-52"}]
        with pytest.raises(ValidationError) as exc_info:
            validate_enclosure_input(main, branches)
        # 일관성: error_code 체크
        assert exc_info.value.error_code.code == "ENC-003"

    def test_invalid_branch_breaker_first(self):
        """오류: 분기 차단기[0] AF-Pole 위반"""
        main = {"frame_af": 100, "poles": 3, "model": "SBE-103"}
        branches = [
            {"frame_af": 400, "poles": 2, "model": "INVALID"},  # 400AF는 2P 불가
            {"frame_af": 50, "poles": 2, "model": "SBE-52"},
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate_enclosure_input(main, branches)
        # 일관성: field에 branch_breakers[0] 포함
        assert "branch_breakers[0]" in exc_info.value.details.get("field", "")

    def test_invalid_branch_breaker_second(self):
        """오류: 분기 차단기[1] AF-Pole 위반"""
        main = {"frame_af": 100, "poles": 3, "model": "SBE-103"}
        branches = [
            {"frame_af": 50, "poles": 2, "model": "SBE-52"},
            {"frame_af": 999, "poles": 2, "model": "INVALID"},  # 잘못된 AF
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate_enclosure_input(main, branches)
        # 일관성: field에 branch_breakers[1] 포함
        assert "branch_breakers[1]" in exc_info.value.details.get("field", "")

    def test_with_customer_requirements_none(self):
        """정상: customer_requirements=None"""
        main = {"frame_af": 100, "poles": 3, "model": "SBE-103"}
        branches = [{"frame_af": 50, "poles": 2, "model": "SBE-52"}]
        validate_enclosure_input(
            main, branches, customer_requirements=None
        )  # 예외 없음

    def test_with_customer_requirements_empty(self):
        """정상: customer_requirements={} (향후 확장)"""
        main = {"frame_af": 100, "poles": 3, "model": "SBE-103"}
        branches = [{"frame_af": 50, "poles": 2, "model": "SBE-52"}]
        validate_enclosure_input(main, branches, customer_requirements={})  # 예외 없음
