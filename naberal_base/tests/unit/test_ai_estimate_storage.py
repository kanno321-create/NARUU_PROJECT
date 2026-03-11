"""
Unit tests for AI Estimate Storage

Tests data flow between AI Chat handlers and storage.
NO MOCKS - Real service operations
"""

from kis_estimator_core.services.ai_estimate_storage import (
    AIEstimateStorage,
    get_ai_estimate_storage,
)


class TestAIEstimateStorage:
    """AI Estimate Storage 테스트"""

    def setup_method(self):
        """각 테스트 전 스토리지 초기화"""
        # 싱글톤 리셋
        AIEstimateStorage._instance = None
        AIEstimateStorage._estimates = {}

    def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        storage1 = get_ai_estimate_storage()
        storage2 = get_ai_estimate_storage()
        assert storage1 is storage2

    def test_save_and_retrieve_estimate(self):
        """견적 저장 및 조회 테스트"""
        storage = get_ai_estimate_storage()

        form_data = {
            "customer": {"company_name": "Test Co", "phone": "010-1234-5678"},
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
                "price": 12500,
            },
            "branch_breakers": [
                {"category": "ELB", "poles": 3, "current_a": 30, "quantity": 5, "model": "SEE-53", "price": 8500}
            ],
        }

        # 저장
        stored = storage.save_estimate("EST-TEST-001", form_data)
        assert stored.estimate_id == "EST-TEST-001"
        assert stored.form_data == form_data
        assert stored.panel_data is not None
        assert stored.placement_result is not None

        # 조회
        retrieved = storage.get_estimate("EST-TEST-001")
        assert retrieved is not None
        assert retrieved.estimate_id == "EST-TEST-001"

    def test_panel_data_generation(self):
        """패널 데이터 자동 생성 테스트"""
        storage = get_ai_estimate_storage()

        form_data = {
            "enclosure": {"type": "옥외노출", "material": "SUS201 1.2T", "width": 700, "height": 1000, "depth": 250},
            "main_breaker": {"brand": "LS", "poles": 4, "current_a": 200, "model": "ABN-204"},
            "branch_breakers": [],
        }

        stored = storage.save_estimate("EST-TEST-002", form_data)

        # panel_data 구조 확인
        assert "name" in stored.panel_data
        assert "enclosure" in stored.panel_data
        assert "main_breaker" in stored.panel_data

        # enclosure 데이터 확인
        enc = stored.panel_data["enclosure"]
        assert enc["width"] == 700
        assert enc["height"] == 1000
        assert enc["type"] == "옥외노출"

    def test_placement_result_generation(self):
        """배치 결과 자동 생성 테스트"""
        storage = get_ai_estimate_storage()

        form_data = {
            "enclosure": {"type": "옥내노출", "material": "STEEL 1.6T"},
            "main_breaker": {"poles": 4, "current_a": 100},
            "branch_breakers": [
                {"category": "ELB", "poles": 3, "current_a": 30, "quantity": 4},
                {"category": "MCCB", "poles": 2, "current_a": 20, "quantity": 6},
            ],
        }

        stored = storage.save_estimate("EST-TEST-003", form_data)

        # placement_result 확인
        assert stored.placement_result is not None
        assert "breakers" in stored.placement_result
        assert stored.placement_result["total_count"] == 10  # 4 + 6

        # 좌우 배치 확인
        left_count = stored.placement_result["left_count"]
        right_count = stored.placement_result["right_count"]
        assert left_count + right_count == 10

    def test_update_drawings(self):
        """도면 업데이트 테스트"""
        storage = get_ai_estimate_storage()

        form_data = {"enclosure": {}, "main_breaker": {"poles": 4, "current_a": 50}, "branch_breakers": []}
        storage.save_estimate("EST-TEST-004", form_data)

        # 도면 업데이트
        drawings = {
            "wiring_diagram": {"path": "drawings/EST-TEST-004_wiring.svg"},
            "enclosure_diagram": {"path": "drawings/EST-TEST-004_enclosure.svg"},
        }
        result = storage.update_drawings("EST-TEST-004", drawings)
        assert result is True

        # 확인
        retrieved = storage.get_estimate("EST-TEST-004")
        assert retrieved.drawings == drawings

    def test_update_pdf_path(self):
        """PDF 경로 업데이트 테스트"""
        storage = get_ai_estimate_storage()

        form_data = {"enclosure": {}, "main_breaker": {"poles": 4, "current_a": 50}, "branch_breakers": []}
        storage.save_estimate("EST-TEST-005", form_data)

        # PDF 경로 업데이트
        result = storage.update_pdf_path("EST-TEST-005", "output/EST-TEST-005.pdf")
        assert result is True

        # 확인
        retrieved = storage.get_estimate("EST-TEST-005")
        assert retrieved.pdf_path == "output/EST-TEST-005.pdf"

    def test_list_estimates(self):
        """견적 목록 조회 테스트"""
        storage = get_ai_estimate_storage()

        # 여러 견적 저장
        for i in range(5):
            form_data = {"enclosure": {}, "main_breaker": {"poles": 4, "current_a": 50}, "branch_breakers": []}
            storage.save_estimate(f"EST-LIST-{i:03d}", form_data)

        # 목록 조회
        estimate_list = storage.list_estimates(3)
        assert len(estimate_list) == 3

        estimate_list_all = storage.list_estimates(10)
        assert len(estimate_list_all) == 5

    def test_get_nonexistent_estimate(self):
        """존재하지 않는 견적 조회 테스트"""
        storage = get_ai_estimate_storage()
        result = storage.get_estimate("EST-NONEXISTENT")
        assert result is None

    def test_update_nonexistent_estimate(self):
        """존재하지 않는 견적 업데이트 테스트"""
        storage = get_ai_estimate_storage()
        result = storage.update_drawings("EST-NONEXISTENT", {})
        assert result is False

        result = storage.update_pdf_path("EST-NONEXISTENT", "path.pdf")
        assert result is False
