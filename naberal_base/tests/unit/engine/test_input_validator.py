"""
Unit Tests: engine/input_validator.py
목표: 13.91% → 80%+
"""

import pytest
from unittest.mock import Mock
from kis_estimator_core.engine.input_validator import InputValidator
from kis_estimator_core.errors import (
    INP_001,
    INP_002,
    INP_003,
    INP_004,
    INP_005,
    BUG_001,
    BUG_002,
    BUG_003,
    BUG_004,
    BUS_001,
    BUS_002,
    BUS_003,
    BUS_004,
)

pytestmark = pytest.mark.unit


class TestInputValidatorInit:
    def test_init(self, monkeypatch):
        """초기화 테스트"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()
        assert validator.ai_catalog == mock_catalog


class TestValidateRequiredInfo:
    def test_all_valid(self, monkeypatch):
        """모든 필수 정보 제공"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[{"poles": 2, "current": 20, "type": "MCCB"}],
        )
        assert passed is True
        assert len(errors) == 0

    def test_missing_enclosure_material(self, monkeypatch):
        """INP-001: 외함 재질 누락"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material=None,
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[{"poles": 2, "current": 20}],
        )
        assert passed is False
        assert any(e.error_code == INP_001 for e in errors)

    def test_missing_enclosure_type(self, monkeypatch):
        """INP-002: 외함 종류 누락"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type=None,
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[{"poles": 2, "current": 20}],
        )
        assert passed is False
        assert any(e.error_code == INP_002 for e in errors)

    def test_missing_breaker_brand(self, monkeypatch):
        """INP-003: 차단기 브랜드 누락"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand=None,
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[{"poles": 2, "current": 20}],
        )
        assert passed is False
        assert any(e.error_code == INP_003 for e in errors)

    def test_missing_main_breaker(self, monkeypatch):
        """INP-004: 메인 차단기 누락"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker=None,
            branch_breakers=[{"poles": 2, "current": 20}],
        )
        assert passed is False
        assert any(e.error_code == INP_004 for e in errors)

    def test_missing_branch_breakers(self, monkeypatch):
        """INP-005: 분기 차단기 누락"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=None,
        )
        assert passed is False
        assert any(e.error_code == INP_005 for e in errors)


class TestMCCBELBDistinction:
    def test_mccb_with_leakage_keyword(self, monkeypatch):
        """BUG-001: MCCB인데 누전 키워드"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[
                {"type": "MCCB", "description": "누전차단기", "poles": 2, "current": 20}
            ],
        )
        assert any(e.error_code == BUG_001 for e in errors)

    def test_elb_without_leakage_keyword(self, monkeypatch):
        """BUG-001: ELB인데 누전 키워드 없음"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[
                {"type": "ELB", "description": "배선용차단기", "poles": 2, "current": 20}
            ],
        )
        assert any(e.error_code == BUG_001 for e in errors)

    def test_valid_mccb(self, monkeypatch):
        """정상 MCCB"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[
                {"type": "MCCB", "description": "배선용차단기", "poles": 2, "current": 20}
            ],
        )
        assert not any(e.error_code == BUG_001 for e in errors)

    def test_valid_elb(self, monkeypatch):
        """정상 ELB"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[
                {"type": "ELB", "description": "누전차단기", "poles": 2, "current": 20}
            ],
        )
        assert not any(e.error_code == BUG_001 for e in errors)


class TestCatalogExistence:
    def test_catalog_not_found(self, monkeypatch):
        """BUG-002: 카탈로그 없음"""
        mock_catalog = Mock()
        mock_catalog.get_breaker_by_spec.return_value = None
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[{"type": "MCCB", "poles": 2, "current": 99999}],
        )
        assert any(e.error_code == BUG_002 for e in errors)

    def test_catalog_found(self, monkeypatch):
        """카탈로그 존재"""
        mock_catalog = Mock()
        mock_catalog.get_breaker_by_spec.return_value = {"model": "SBE-52"}
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[{"type": "MCCB", "poles": 2, "current": 20}],
        )
        assert not any(e.error_code == BUG_002 for e in errors)


class TestBreakerTypeSelection:
    def test_small_breaker_required(self, monkeypatch):
        """BUG-003: 2P 20A는 소형 필요"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[
                {"type": "MCCB", "poles": 2, "current": 20, "model": "SBE-52"}
            ],
        )
        assert any(e.error_code == BUG_003 for e in errors)

    def test_compact_breaker_required(self, monkeypatch):
        """BUG-004: 2P 40A는 컴팩트 필요"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[
                {"type": "MCCB", "poles": 2, "current": 40, "model": "SBE-52"}
            ],
        )
        assert any(e.error_code == BUG_004 for e in errors)

    def test_valid_small_breaker(self, monkeypatch):
        """정상 소형 차단기"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[
                {"type": "MCCB", "poles": 2, "current": 20, "model": "SIB-32"}
            ],
        )
        assert not any(e.error_code == BUG_003 for e in errors)

    def test_valid_compact_breaker(self, monkeypatch):
        """정상 컴팩트 차단기"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[
                {"type": "MCCB", "poles": 2, "current": 40, "model": "SBC-52"}
            ],
        )
        assert not any(e.error_code == BUG_004 for e in errors)


class TestMainBusbarSpec:
    def test_busbar_50_125af_invalid(self, monkeypatch):
        """BUS-001: 50~125AF는 3T*15 필요"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[{"type": "MCCB", "poles": 2, "current": 20}],
            accessories=[{"name": "MAIN BUS-BAR", "spec": "5T*20"}],
        )
        assert any(e.error_code == BUS_001 for e in errors)

    def test_busbar_200_250af_invalid(self, monkeypatch):
        """BUS-002: 200~250AF는 5T*20 필요"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 200, "frame": 200},
            branch_breakers=[{"type": "MCCB", "poles": 2, "current": 20}],
            accessories=[{"name": "MAIN BUS-BAR", "spec": "3T*15"}],
        )
        assert any(e.error_code == BUS_002 for e in errors)

    def test_busbar_400af_invalid(self, monkeypatch):
        """BUS-003: 400AF는 6T*30 필요"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 300, "frame": 400},
            branch_breakers=[{"type": "MCCB", "poles": 2, "current": 20}],
            accessories=[{"name": "MAIN BUS-BAR", "spec": "5T*20"}],
        )
        assert any(e.error_code == BUS_003 for e in errors)

    def test_busbar_600_800af_invalid(self, monkeypatch):
        """BUS-004: 600~800AF는 8T*40 필요"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 600, "frame": 600},
            branch_breakers=[{"type": "MCCB", "poles": 2, "current": 20}],
            accessories=[{"name": "MAIN BUS-BAR", "spec": "6T*30"}],
        )
        assert any(e.error_code == BUS_004 for e in errors)

    def test_valid_busbar_spec(self, monkeypatch):
        """정상 BUS-BAR 규격"""
        mock_catalog = Mock()
        monkeypatch.setattr(
            "kis_estimator_core.engine.input_validator.get_ai_catalog_service",
            lambda: mock_catalog,
        )
        validator = InputValidator()

        passed, errors = validator.validate(
            enclosure_material="STEEL 1.6T",
            enclosure_type="옥내노출",
            breaker_brand="상도차단기",
            main_breaker={"poles": 4, "current": 60, "frame": 100},
            branch_breakers=[{"type": "MCCB", "poles": 2, "current": 20}],
            accessories=[{"name": "MAIN BUS-BAR", "spec": "3T*15"}],
        )
        assert not any(e.error_code in [BUS_001, BUS_002, BUS_003, BUS_004] for e in errors)
