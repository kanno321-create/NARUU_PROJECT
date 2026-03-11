"""
REGISTRY Single Source Tests (I-3.3)

LAW-06: REGISTRY는 factory.py에 고정된 단일 소스
동적 등록 금지, 중복 키 재정의 금지
"""

import pytest
from kis_estimator_core.engine.verbs.factory import get_registry, register_verb
from kis_estimator_core.engine.verbs.base import BaseVerb


class TestRegistrySingleSource:
    """REGISTRY 단일 소스 검증 테스트"""

    def test_registry_is_fixed_dict(self):
        """REGISTRY는 고정된 dict이며 예상 Verb를 포함"""
        registry = get_registry()
        assert isinstance(registry, dict)
        assert "PICK_ENCLOSURE" in registry
        assert "PLACE" in registry
        assert len(registry) == 2  # I-3.3 시점에서 2개만 등록

    def test_registry_entries_are_verb_classes(self):
        """REGISTRY 값은 모두 BaseVerb 서브클래스"""
        registry = get_registry()
        for verb_name, verb_class in registry.items():
            assert issubclass(
                verb_class, BaseVerb
            ), f"{verb_name} is not BaseVerb subclass"

    def test_registry_keys_are_uppercase(self):
        """REGISTRY 키는 모두 대문자"""
        registry = get_registry()
        for verb_name in registry.keys():
            assert verb_name.isupper(), f"{verb_name} is not uppercase"
            assert verb_name == verb_name.upper()

    def test_registry_has_correct_mappings(self):
        """REGISTRY 매핑 정확성 검증"""
        registry = get_registry()
        # Lazy import로 인해 클래스 직접 비교 대신 이름으로 검증
        assert "PickEnclosureVerb" in registry["PICK_ENCLOSURE"].__name__
        assert "PlaceVerb" in registry["PLACE"].__name__

    def test_register_verb_is_deprecated_and_logs_warning(self, caplog):
        """register_verb() 호출 시 deprecated 경고 로그"""

        # I-3.3: register_verb()는 deprecated이지만 호출은 가능 (경고만)
        class DummyVerb(BaseVerb):
            def execute(self):
                return {}

        with caplog.at_level("WARNING"):
            register_verb("DUMMY", DummyVerb)

        # 경고 로그 확인
        assert any("DEPRECATED" in record.message for record in caplog.records)
        assert any("register_verb" in record.message for record in caplog.records)

    def test_registry_immutability_intention(self):
        """REGISTRY는 의도적으로 불변이어야 함 (LAW-06)"""
        # I-3.3: REGISTRY는 고정 dict이므로 외부에서 수정 금지
        # 이 테스트는 "의도" 검증 - 실제 런타임에서 dict는 mutable이지만
        # 코드 규약상 수정하지 않는다는 것을 문서화

        registry = get_registry()
        original_keys = set(registry.keys())

        # 임의로 키 추가 시도 (규약 위반 시뮬레이션)
        class BadVerb(BaseVerb):
            def execute(self):
                return {}

        # 직접 수정은 기술적으로 가능하지만 LAW-06 위반
        registry["BAD_VERB"] = BadVerb

        # 정리 (테스트 격리)
        del registry["BAD_VERB"]

        # 원래 키 세트로 복원 확인
        assert set(registry.keys()) == original_keys

    def test_no_duplicate_verb_names_in_registry(self):
        """REGISTRY에 중복 verb_name 없음"""
        registry = get_registry()
        verb_names = list(registry.keys())
        assert len(verb_names) == len(
            set(verb_names)
        ), "Duplicate verb_name in REGISTRY"

    def test_registry_only_contains_implemented_verbs(self):
        """REGISTRY는 실제 구현된 Verb만 포함 (TODO 주석은 미등록)"""
        # I-3.3 시점: PICK_ENCLOSURE, PLACE만 구현
        # REBALANCE, TRY는 TODO 주석만 존재 → REGISTRY에 없어야 함
        registry = get_registry()
        assert "REBALANCE" not in registry
        assert "TRY" not in registry

    def test_from_spec_uses_registry_only(self, mock_ctx):
        """from_spec()은 REGISTRY만 참조 (동적 등록 무시)"""
        from kis_estimator_core.engine.verbs.factory import from_spec

        # 정상 등록 Verb는 성공
        valid_spec = {
            "verb_name": "PICK_ENCLOSURE",
            "params": {
                "main_breaker": {"poles": 4, "current": 100},
                "branch_breakers": [],
                "enclosure_type": "옥내노출",
                "material": "STEEL",
                "thickness": "1.6T",
            },
            "version": "1.0.0",
        }

        verb = from_spec(valid_spec, ctx=mock_ctx)
        assert verb is not None

        # 미등록 Verb는 실패 (register_verb 호출해도 REGISTRY 고정이므로 실패해야 함)
        class UnregisteredVerb(BaseVerb):
            def execute(self):
                return {}

        register_verb("UNREGISTERED", UnregisteredVerb)  # deprecated, 무시됨

        invalid_spec = {"verb_name": "UNREGISTERED", "params": {}, "version": "1.0.0"}

        with pytest.raises(Exception) as exc_info:
            from_spec(invalid_spec, ctx=mock_ctx)

        # VERB-002 또는 unknown verb 에러
        assert "VERB-002" in str(exc_info.value) or "Unknown verb" in str(
            exc_info.value
        )


@pytest.fixture
def mock_ctx():
    """Mock ExecutionCtx"""
    import logging
    from types import SimpleNamespace
    from kis_estimator_core.engine.context import ExecutionCtx

    ssot = SimpleNamespace()
    logger = logging.getLogger("test")
    return ExecutionCtx(ssot=ssot, db=None, logger=logger, state={})
