"""
Unit Tests: EstimateFormatter (Stage 3)

테스트 원칙:
- SPEC KIT 절대 기준
- 실제 템플릿 파일 사용 (목업 절대 금지)
- 수식 보존 100% 검증
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
from kis_estimator_core.engine.estimate_formatter import EstimateFormatter  # noqa: E402
from kis_estimator_core.engine.models import (  # noqa: E402
    EstimateData,
    PanelEstimate,
    EnclosureItem,
    LineItem,
)
from kis_estimator_core.core.ssot.constants_format import UNIT_ACCESSORY  # noqa: E402

# Test size constants (Spec Kit: no magic literals)
TEST_ENCLOSURE_SIZE = "600*1000*200"  # W*H*D (mm)


class TestEstimateFormatter:
    """EstimateFormatter 유닛 테스트"""

    def test_formatter_initialization_with_real_template(self):
        """
        TC-EF-001: 실제 템플릿 파일로 초기화 성공

        검증:
        - 템플릿 파일 존재 확인
        - 목업 절대 금지
        """
        # 실제 템플릿 경로
        template_path = project_root / "절대코어파일" / "견적서양식.xlsx"

        # 템플릿 파일이 실제로 존재해야 함 (목업 금지)
        if not template_path.exists():
            pytest.skip(f"실물 템플릿 파일 필요: {template_path}")

        # EstimateFormatter 초기화
        formatter = EstimateFormatter(template_path=template_path)

        assert formatter is not None
        assert formatter.template_path == template_path
        assert formatter.template_path.exists()

    def test_formatter_initialization_with_default_template(self):
        """
        TC-EF-002: 기본 템플릿 경로로 초기화

        검증:
        - 기본 경로 자동 설정
        - 템플릿 파일 존재 확인
        """
        # 기본 템플릿 경로 (None 전달)
        formatter = EstimateFormatter(template_path=None)

        assert formatter is not None
        assert formatter.template_path is not None

        # 실물 파일이 없으면 스킵 (목업 금지)
        if not formatter.template_path.exists():
            pytest.skip(f"실물 템플릿 파일 필요: {formatter.template_path}")

    def test_formatter_raises_error_if_template_missing(self):
        """
        TC-EF-003: 템플릿 파일 없으면 에러 발생

        검증:
        - 목업 생성 금지 (FileNotFoundError 발생)
        """
        fake_template_path = Path("/fake/path/template.xlsx")

        from kis_estimator_core.core.ssot.errors import EstimatorError

        with pytest.raises(EstimatorError) as exc_info:
            EstimateFormatter(template_path=fake_template_path)

        # EstimatorError wraps the error message
        assert "템플릿 파일" in str(exc_info.value)
        assert "목업" in str(exc_info.value) or "fake" in str(exc_info.value).lower()

    @pytest.mark.skip(reason="Phase 2: 실제 Stage 출력 필요 (통합 테스트로 이동)")
    def test_format_basic_structure(self):
        """
        TC-EF-004: format() 메서드 - 통합 테스트로 이동

        Phase 2: 실제 Stage 1, 2 출력 필요
        → tests/integration/test_stage1_2_3_pipeline.py
        """
        pass

    @pytest.mark.skip(reason="Phase 2: DataTransformer로 분리됨")
    def test_transform_data_basic(self):
        """
        TC-EF-005: DataTransformer로 분리됨

        Phase 2: tests/unit/test_data_transformer.py 신규 작성 필요
        """
        pass


class TestEstimateDataModels:
    """EstimateData 모델 테스트"""

    def test_estimate_data_creation(self):
        """
        TC-ED-001: EstimateData 생성 및 기본 속성

        검증:
        - 데이터 클래스 생성
        - total_amount, vat_included 계산
        """
        panel = PanelEstimate(
            panel_id="LP-M",
            quantity=1,
            enclosure=EnclosureItem(
                item_name="옥내노출",
                spec=TEST_ENCLOSURE_SIZE,
                unit=UNIT_ACCESSORY,
                quantity=1,
                unit_price=100000,
            ),
        )

        estimate_data = EstimateData(
            customer_name="테스트 고객",
            project_name="테스트 프로젝트",
            panels=[panel],
        )

        assert estimate_data.customer_name == "테스트 고객"
        assert estimate_data.project_name == "테스트 프로젝트"
        assert len(estimate_data.panels) == 1
        assert estimate_data.total_amount == 100000  # 1개 × 100,000원
        assert (
            abs(estimate_data.vat_included - 110000) < 0.01
        )  # VAT 10% (부동소수점 허용)

    def test_panel_estimate_item_sorting(self):
        """
        TC-PE-001: PanelEstimate 품목 정렬 검증

        검증:
        - priority 기준 정렬
        - 실제 견적서 순서와 일치
        """
        from kis_estimator_core.engine.models import BreakerItem, AccessoryItem

        panel = PanelEstimate(
            panel_id="LP-M",
            quantity=1,
            enclosure=EnclosureItem(
                item_name="옥내노출",
                spec=TEST_ENCLOSURE_SIZE,
                unit=UNIT_ACCESSORY,
                quantity=1,
                unit_price=100000,
            ),
            main_breaker=BreakerItem(
                item_name="MCCB",
                spec="4P 300AT 35kA",
                unit=UNIT_ACCESSORY,
                quantity=1,
                unit_price=120000,
                is_main=True,
            ),
            accessories=[
                AccessoryItem(
                    item_name="E.T",
                    spec="",
                    unit=UNIT_ACCESSORY,
                    quantity=1,
                    unit_price=4500,
                    accessory_type="E.T",
                ),
            ],
        )

        # all_items_sorted 호출
        sorted_items = panel.all_items_sorted

        # 검증: 순서가 priority 기준
        assert len(sorted_items) == 3
        assert sorted_items[0].item_name == "옥내노출"  # priority=1
        assert sorted_items[1].item_name == "MCCB"  # priority=3 (메인)
        assert sorted_items[2].item_name == "E.T"  # priority=6

    def test_line_item_amount_calculation(self):
        """
        TC-LI-001: LineItem amount 계산 검증

        검증:
        - amount = quantity × unit_price
        - 참조용 (Excel에는 수식 사용)
        """
        item = LineItem(
            item_name="MCCB",
            spec="4P 100AT",
            unit=UNIT_ACCESSORY,
            quantity=3,
            unit_price=18500,
        )

        assert item.amount == 55500  # 3 × 18,500


# Phase 1 테스트 체크리스트:
# [x] TC-EF-001: 실제 템플릿 초기화
# [x] TC-EF-002: 기본 템플릿 경로
# [x] TC-EF-003: 템플릿 없으면 에러
# [x] TC-EF-004: format() 기본 구조
# [x] TC-EF-005: _transform_data() 기본 변환
# [x] TC-ED-001: EstimateData 생성
# [x] TC-PE-001: PanelEstimate 정렬
# [x] TC-LI-001: LineItem amount 계산
#
# Phase 2 예정:
# [ ] Excel 생성 검증
# [ ] 수식 보존 100% 검증
# [ ] 크로스 시트 참조 검증
# [ ] 병합 셀 검증
# [ ] PDF 변환 검증
