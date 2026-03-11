"""
VerbFactory Validation Tests (I-3.3)

Tests:
- 미등록 verb_name → VERB-002
- params 누락/타입 불일치 → VALIDATION_VERB-001
- 정상 spec → BaseVerb 인스턴스
"""

import pytest
from types import SimpleNamespace
from kis_estimator_core.engine.verbs.factory import from_spec
from kis_estimator_core.engine.context import ExecutionCtx
from kis_estimator_core.core.ssot.errors import EstimatorError
from kis_estimator_core.engine.verbs.base import BaseVerb


@pytest.fixture
def mock_ctx():
    """Mock ExecutionCtx"""
    import logging

    ssot = SimpleNamespace()
    logger = logging.getLogger("test")
    return ExecutionCtx(ssot=ssot, db=None, logger=logger, state={})


class TestFactoryValidation:
    """VerbFactory SSOT 검증 테스트"""

    def test_unknown_verb_raises_verb_002(self, mock_ctx):
        """미등록 verb_name → VERB-002 에러"""
        spec = {"verb_name": "UNKNOWN_VERB", "params": {}, "version": "1.0.0"}

        with pytest.raises(EstimatorError) as exc_info:
            from_spec(spec, ctx=mock_ctx)

        # ErrorCode.VERB_002 검증
        error_msg = str(exc_info.value)
        assert "VERB-002" in error_msg or "Unknown verb" in error_msg

    def test_missing_required_param_raises_validation_verb_001(self, mock_ctx):
        """필수 params 누락 → VALIDATION-VERB-001 에러"""
        spec = {
            "verb_name": "PICK_ENCLOSURE",
            "params": {
                # main_breaker 누락 (required)
                "branch_breakers": [],
                "enclosure_type": "옥내노출",
                "material": "STEEL",
                "thickness": "1.6T",
            },
            "version": "1.0.0",
        }

        with pytest.raises(EstimatorError) as exc_info:
            from_spec(spec, ctx=mock_ctx)

        # VALIDATION-VERB-001 검증
        error_msg = str(exc_info.value)
        assert "VALIDATION-VERB-001" in error_msg or "validation" in error_msg.lower()

    def test_invalid_param_type_raises_validation_verb_001(self, mock_ctx):
        """params 타입 불일치 → VALIDATION-VERB-001 에러"""
        spec = {
            "verb_name": "PLACE",
            "params": {
                "breakers": "not_a_list",  # should be List[Any]
                "panel": "default",
                "strategy": "compact",
                "algo": "heuristic",
                "seed": 42,
            },
            "version": "1.0.0",
        }

        with pytest.raises(EstimatorError) as exc_info:
            from_spec(spec, ctx=mock_ctx)

        # VALIDATION-VERB-001 검증
        error_msg = str(exc_info.value)
        assert "VALIDATION-VERB-001" in error_msg or "validation" in error_msg.lower()

    def test_valid_pick_enclosure_spec_returns_verb_instance(self, mock_ctx):
        """정상 PICK_ENCLOSURE spec → BaseVerb 인스턴스"""
        spec = {
            "verb_name": "PICK_ENCLOSURE",
            "params": {
                "main_breaker": {"poles": 4, "current": 100, "frame": "100AF"},
                "branch_breakers": [{"id": "BR1", "poles": 2, "current": 30}],
                "enclosure_type": "옥내노출",
                "material": "STEEL",
                "thickness": "1.6T",
                "accessories": [],
                "panel": "default",
                "strategy": "auto",
            },
            "version": "1.0.0",
        }

        verb = from_spec(spec, ctx=mock_ctx)

        assert isinstance(verb, BaseVerb)
        assert verb.__class__.__name__ == "PickEnclosureVerb"

    def test_valid_place_spec_returns_verb_instance(self, mock_ctx):
        """정상 PLACE spec → BaseVerb 인스턴스"""
        spec = {
            "verb_name": "PLACE",
            "params": {
                "breakers": ["MAIN", "BR1", "BR2"],
                "panel": "default",
                "strategy": "compact",
                "algo": "heuristic",
                "seed": 42,
            },
            "version": "1.0.0",
        }

        verb = from_spec(spec, ctx=mock_ctx)

        assert isinstance(verb, BaseVerb)
        assert verb.__class__.__name__ == "PlaceVerb"

    def test_valid_spec_with_minimal_params(self, mock_ctx):
        """최소 필수 params만 제공 → 성공 (optional은 기본값)"""
        spec = {
            "verb_name": "PICK_ENCLOSURE",
            "params": {
                "main_breaker": {"poles": 3, "current": 200},
                "branch_breakers": [],
                "enclosure_type": "옥외노출",
                "material": "SUS201",
                "thickness": "1.2T",
                # accessories, panel, strategy는 기본값 사용
            },
            "version": "1.0.0",
        }

        verb = from_spec(spec, ctx=mock_ctx)

        assert isinstance(verb, BaseVerb)

    def test_invalid_verb_spec_structure_raises_validation_verb_001(self, mock_ctx):
        """VerbSpec 구조 오류 → VALIDATION-VERB-001 에러"""
        spec = {
            "verb_name": "PICK_ENCLOSURE",
            # params 누락 (VerbSpecModel 필수 필드)
            "version": "1.0.0",
        }

        with pytest.raises(EstimatorError) as exc_info:
            from_spec(spec, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "VALIDATION-VERB-001" in error_msg or "validation" in error_msg.lower()
