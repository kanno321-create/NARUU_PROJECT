"""
Unit tests for AI Chat Confirm Feature

Tests NLP parsing and parameter extraction for estimate confirmation.
NO MOCKS - Real service operations

NOTE: These tests are for the 'confirm' intent feature which is NOT YET IMPLEMENTED.
The NLPParser.INTENT_KEYWORDS does not have 'confirm' key yet.
Marked as not_implemented to exclude from CI until feature is implemented.
"""

import pytest

from kis_estimator_core.api.routes.ai_chat import (
    NLPParser,
)
from kis_estimator_core.services.ai_estimate_storage import (
    AIEstimateStorage,
    get_ai_estimate_storage,
)

# Mark all tests in this module as not_implemented
# These tests are for features that don't exist yet
pytestmark = pytest.mark.not_implemented


class TestConfirmIntentParsing:
    """견적 확정 인텐트 파싱 테스트"""

    def test_confirm_intent_keywords(self):
        """confirm 인텐트 키워드 존재 확인"""
        assert "confirm" in NLPParser.INTENT_KEYWORDS
        keywords = NLPParser.INTENT_KEYWORDS["confirm"]
        assert "확정" in keywords
        assert "최종" in keywords
        assert "파이프라인" in keywords

    def test_parse_confirm_intent_korean(self):
        """한국어 확정 요청 파싱"""
        test_cases = [
            "EST-20251128022306 확정해줘",
            "이 견적 확정해",
            "최종 견적 생성",
            "파이프라인 실행해줘",
        ]

        for text in test_cases:
            result = NLPParser.parse(text)
            assert result.intent == "confirm", f"Failed for: {text}"

    def test_parse_confirm_intent_english(self):
        """영어 확정 요청 파싱"""
        test_cases = [
            "confirm EST-20251128022306",
            "finalize the estimate",
            "run fix-4 pipeline",
        ]

        for text in test_cases:
            result = NLPParser.parse(text)
            assert result.intent == "confirm", f"Failed for: {text}"


class TestConfirmParameterExtraction:
    """견적 확정 파라미터 추출 테스트"""

    def test_extract_estimate_id_full_format(self):
        """전체 형식 견적 ID 추출 (14자리)"""
        params = NLPParser._extract_confirm_params("EST-20251128022306 확정해줘")
        assert params.get("estimate_id") == "EST-20251128022306"

    def test_extract_estimate_id_short_format(self):
        """짧은 형식 견적 ID 추출 (8자리)"""
        params = NLPParser._extract_confirm_params("EST-20251128 확정")
        assert params.get("estimate_id") == "EST-20251128"

    def test_extract_estimate_id_lowercase(self):
        """소문자 견적 ID 대문자 변환"""
        params = NLPParser._extract_confirm_params("est-20251128022306 확정")
        assert params.get("estimate_id") == "EST-20251128022306"

    def test_extract_no_estimate_id(self):
        """견적 ID 없는 경우"""
        params = NLPParser._extract_confirm_params("최종 견적 확정해줘")
        assert "estimate_id" not in params


class TestConfirmIntentParams:
    """ParsedIntent에 confirm 파라미터 포함 테스트"""

    def test_parsed_intent_with_estimate_id(self):
        """견적 ID가 포함된 ParsedIntent"""
        result = NLPParser.parse("EST-20251128022306 확정해줘")
        assert result.intent == "confirm"
        assert result.params.get("estimate_id") == "EST-20251128022306"

    def test_parsed_intent_without_estimate_id(self):
        """견적 ID 없는 ParsedIntent (자동 선택 대상)"""
        result = NLPParser.parse("견적 확정해")
        assert result.intent == "confirm"
        # estimate_id가 없으면 최근 견적 자동 선택


class TestConfirmWithStorage:
    """스토리지 연동 확정 테스트"""

    def setup_method(self):
        """각 테스트 전 스토리지 초기화"""
        AIEstimateStorage._instance = None
        AIEstimateStorage._estimates = {}

    def test_confirm_requires_stored_estimate(self):
        """확정 시 저장된 견적 필요"""
        storage = get_ai_estimate_storage()

        # 견적 없이 조회
        result = storage.get_estimate("EST-NONEXISTENT")
        assert result is None

    def test_confirm_with_valid_estimate(self):
        """유효한 견적으로 확정 준비"""
        storage = get_ai_estimate_storage()

        # 견적 저장
        form_data = {
            "customer": {"company_name": "테스트 전기"},
            "enclosure": {
                "type": "옥내노출",
                "material": "STEEL 1.6T",
                "width": 600,
                "height": 800,
                "depth": 200,
            },
            "main_breaker": {
                "brand": "상도",
                "series": "경제형",
                "category": "MCCB",
                "poles": 4,
                "current_a": 100,
                "model": "SBE-104",
                "price": 18000,
            },
            "branch_breakers": [
                {
                    "category": "ELB",
                    "poles": 3,
                    "current_a": 30,
                    "quantity": 5,
                    "model": "SEE-53",
                    "price": 8500,
                }
            ],
        }
        stored = storage.save_estimate("EST-20251128090000", form_data)

        # 견적 조회 확인
        retrieved = storage.get_estimate("EST-20251128090000")
        assert retrieved is not None
        assert retrieved.estimate_id == "EST-20251128090000"
        assert retrieved.form_data == form_data
        assert retrieved.panel_data is not None

    def test_auto_select_single_estimate(self):
        """견적 1개일 때 자동 선택 로직"""
        storage = get_ai_estimate_storage()

        # 견적 1개 저장
        form_data = {
            "enclosure": {"type": "옥내노출", "material": "STEEL 1.6T"},
            "main_breaker": {"poles": 4, "current_a": 100},
            "branch_breakers": [],
        }
        storage.save_estimate("EST-AUTO-SELECT", form_data)

        # 목록 조회 시 1개만 반환
        estimates = storage.list_estimates(5)
        assert len(estimates) == 1
        assert estimates[0] == "EST-AUTO-SELECT"


class TestConfirmDataConversion:
    """StoredEstimate → EstimateRequest 변환 테스트"""

    def setup_method(self):
        """각 테스트 전 스토리지 초기화"""
        AIEstimateStorage._instance = None
        AIEstimateStorage._estimates = {}

    def test_form_data_to_estimate_request_structure(self):
        """form_data → EstimateRequest 구조 변환"""
        storage = get_ai_estimate_storage()

        form_data = {
            "customer": {"company_name": "변환 테스트"},
            "enclosure": {
                "type": "옥내노출",
                "material": "STEEL 1.6T",
                "width": 600,
                "height": 800,
                "depth": 200,
            },
            "main_breaker": {
                "brand": "상도",
                "series": "경제형",
                "category": "MCCB",
                "poles": 4,
                "current_a": 100,
                "model": "SBE-104",
                "price": 18000,
            },
            "branch_breakers": [
                {
                    "category": "ELB",
                    "poles": 3,
                    "current_a": 30,
                    "quantity": 5,
                    "model": "SEE-53",
                    "price": 8500,
                }
            ],
        }
        stored = storage.save_estimate("EST-CONVERT-TEST", form_data)

        # panel_data 구조 확인
        assert "enclosure" in stored.panel_data
        assert "main_breaker" in stored.panel_data

        # placement_result 구조 확인
        assert "breakers" in stored.placement_result
        assert stored.placement_result["total_count"] == 5  # 5개 분기

    def test_enclosure_type_mapping(self):
        """외함 타입 매핑 확인"""
        valid_types = ["옥내노출", "옥내매입", "옥외노출", "옥외자립"]

        for enc_type in valid_types:
            storage = get_ai_estimate_storage()
            AIEstimateStorage._instance = None
            AIEstimateStorage._estimates = {}

            storage = get_ai_estimate_storage()
            form_data = {
                "enclosure": {"type": enc_type, "material": "STEEL 1.6T"},
                "main_breaker": {"poles": 4, "current_a": 100},
                "branch_breakers": [],
            }
            stored = storage.save_estimate(f"EST-TYPE-{enc_type}", form_data)
            assert stored.panel_data["enclosure"]["type"] == enc_type

    def test_breaker_data_expansion(self):
        """분기차단기 quantity 확장"""
        storage = get_ai_estimate_storage()

        form_data = {
            "enclosure": {"type": "옥내노출", "material": "STEEL 1.6T"},
            "main_breaker": {"poles": 4, "current_a": 100},
            "branch_breakers": [
                {"category": "ELB", "poles": 3, "current_a": 30, "quantity": 3},
                {"category": "MCCB", "poles": 2, "current_a": 20, "quantity": 2},
            ],
        }
        stored = storage.save_estimate("EST-EXPAND-TEST", form_data)

        # 총 5개 (3 + 2)로 확장
        assert stored.placement_result["total_count"] == 5
        assert len(stored.placement_result["breakers"]) == 5
