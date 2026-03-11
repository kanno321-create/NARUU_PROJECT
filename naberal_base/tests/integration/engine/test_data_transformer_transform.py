"""

# Catalog dependency → requires DB
# Skip in CI: requires real Supabase catalog with AUTO model resolution

Tests for DataTransformer.transform method (end-to-end integration).

Zero-Mock Policy: Uses real Supabase catalog_service.
"""

import os
import pytest

pytestmark = [
    pytest.mark.requires_db,
    pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Skipping data transformer tests in CI - requires real Supabase catalog"
    )
]

from kis_estimator_core.engine.data_transformer import DataTransformer


class MockDimensions:
    """Mock dimensions for testing."""

    def __init__(self, width: int, height: int, depth: int):
        self.width_mm = width
        self.height_mm = height
        self.depth_mm = depth


class MockEnclosureResult:
    """Mock enclosure result for testing."""

    def __init__(
        self,
        width: int,
        height: int,
        depth: int,
        enclosure_type: str = "옥내노출",
        material: str = "STEEL 1.6T",
    ):
        self.dimensions = MockDimensions(width, height, depth)
        self.enclosure_type = enclosure_type
        self.material = material


class MockPlacement:
    """Mock breaker placement for testing."""

    def __init__(
        self,
        breaker_id: str,
        row: int = 0,
        model: str = "AUTO",
        poles: int = 4,
        current_a: float = 60.0,
        breaking_capacity_ka: float = 35.0,
    ):
        self.breaker_id = breaker_id
        self.position = {"row": row}
        self.model = model
        self.poles = poles
        self.current_a = current_a
        self.breaking_capacity_ka = breaking_capacity_ka


class MockBreakerInput:
    """Mock original breaker input for testing."""

    def __init__(self, id: str, model: str = "AUTO"):
        self.id = id
        self.model = model


class TestDataTransformerTransform:
    """transform method integration tests."""

    def test_transform_main_only_100af(self):
        """
        통합 테스트: 메인차단기만 (100AF).
        외함 + 메인 + E.T + N.P + 잡자재비 + ASSEMBLY CHARGE.
        """
        transformer = DataTransformer()

        # 입력 데이터
        placements = [
            MockPlacement(
                breaker_id="MAIN-1", row=0, model="AUTO", poles=4, current_a=60.0
            )
        ]
        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        breakers = [MockBreakerInput(id="MAIN-1", model="AUTO")]

        # 변환 실행
        estimate_data = transformer.transform(
            placements=placements,
            enclosure_result=enclosure_result,
            breakers=breakers,
            customer_name="테스트 고객",
            project_name="테스트 프로젝트",
        )

        # 검증
        assert estimate_data is not None
        assert estimate_data.customer_name == "테스트 고객"
        assert estimate_data.project_name == "테스트 프로젝트"
        assert len(estimate_data.panels) == 1

        panel = estimate_data.panels[0]
        assert panel.quantity == 1
        assert panel.enclosure is not None
        assert panel.main_breaker is not None
        assert len(panel.branch_breakers) == 0  # 메인만
        # CEO 규칙 (2024-12-03): 분기차단기 없으면 부스바도 없음
        assert panel.busbar is None  # 메인만: 부스바 없음
        assert panel.assembly_charge is not None

        # 부속자재 확인 (메인만: E.T + N.P + 잡자재비)
        assert len(panel.accessories) == 3

    def test_transform_general_estimate_with_branches(self):
        """
        통합 테스트: 일반 견적 (메인 + 분기 5개).
        """
        transformer = DataTransformer()

        # 입력 데이터
        placements = [
            MockPlacement(breaker_id="MAIN-1", row=0, poles=4, current_a=75.0),
            MockPlacement(breaker_id="BR-1", row=1, poles=2, current_a=30.0),
            MockPlacement(breaker_id="BR-2", row=2, poles=2, current_a=30.0),
            MockPlacement(breaker_id="BR-3", row=3, poles=3, current_a=50.0),
            MockPlacement(breaker_id="BR-4", row=4, poles=3, current_a=50.0),
            MockPlacement(breaker_id="BR-5", row=5, poles=4, current_a=60.0),
        ]
        enclosure_result = MockEnclosureResult(width=700, height=900, depth=250)
        breakers = [
            MockBreakerInput(id="MAIN-1"),
            MockBreakerInput(id="BR-1"),
            MockBreakerInput(id="BR-2"),
            MockBreakerInput(id="BR-3"),
            MockBreakerInput(id="BR-4"),
            MockBreakerInput(id="BR-5"),
        ]

        # 변환 실행
        estimate_data = transformer.transform(
            placements=placements,
            enclosure_result=enclosure_result,
            breakers=breakers,
            customer_name="일반 고객",
            project_name="일반 프로젝트",
        )

        # 검증
        assert estimate_data is not None
        assert len(estimate_data.panels) == 1

        panel = estimate_data.panels[0]
        assert panel.main_breaker is not None
        # 시스템은 동일 규격 차단기를 그룹화하여 quantity로 집계함
        # 5개 placement → 3개 breaker item (2P 30A×2, 3P 50A×2, 4P 60A×1)
        assert len(panel.branch_breakers) == 3
        # 전체 분기 차단기 수량 합계 = 5
        total_branch_qty = sum(b.quantity for b in panel.branch_breakers)
        assert total_branch_qty == 5
        assert panel.busbar is not None  # MAIN BUS-BAR

        # 부속자재 확인 (일반: E.T + N.T + N.P×2 + COATING + P-COVER + INSULATOR + BUS-BAR + 잡자재비)
        # 최소 8개 이상
        assert len(panel.accessories) >= 8

        # 전체 품목 수 확인 (all_items_sorted)
        all_items = panel.all_items_sorted
        assert len(all_items) > 0

    def test_transform_400af_main_only(self):
        """
        통합 테스트: 메인차단기만 (400AF).
        frame_af 속성 설정 여부에 따라 부스바 처리가 선택적으로 적용됨.
        """
        transformer = DataTransformer()

        # 입력 데이터
        placements = [
            MockPlacement(breaker_id="MAIN-1", row=0, poles=4, current_a=300.0)
        ]
        enclosure_result = MockEnclosureResult(width=800, height=900, depth=250)
        breakers = [MockBreakerInput(id="MAIN-1")]

        # 변환 실행
        estimate_data = transformer.transform(
            placements=placements,
            enclosure_result=enclosure_result,
            breakers=breakers,
            customer_name="400AF 고객",
        )

        # 검증
        panel = estimate_data.panels[0]
        assert panel.main_breaker is not None
        assert panel.assembly_charge is not None

        # 부속자재 확인 (메인만: 최소 E.T + N.P + 잡자재비)
        assert len(panel.accessories) >= 3

    def test_transform_large_estimate_48_breakers(self):
        """
        통합 테스트: 대규모 견적 (메인 + 분기 48개).
        E.T 수량 공식: 48개 → (48 ÷ 12) + 1 = 5개.
        """
        transformer = DataTransformer()

        # 메인 1개 + 분기 48개
        placements = [
            MockPlacement(breaker_id="MAIN-1", row=0, poles=4, current_a=100.0)
        ]
        for i in range(1, 49):
            placements.append(
                MockPlacement(breaker_id=f"BR-{i}", row=i, poles=2, current_a=30.0)
            )

        enclosure_result = MockEnclosureResult(width=800, height=1200, depth=300)
        breakers = [MockBreakerInput(id="MAIN-1")] + [
            MockBreakerInput(id=f"BR-{i}") for i in range(1, 49)
        ]

        # 변환 실행
        estimate_data = transformer.transform(
            placements=placements,
            enclosure_result=enclosure_result,
            breakers=breakers,
            customer_name="대규모 고객",
        )

        # 검증
        panel = estimate_data.panels[0]
        # 시스템은 동일 규격 차단기를 그룹화함
        # 48개 동일 2P 30A 차단기 → 1개 breaker item with quantity=48
        assert len(panel.branch_breakers) == 1
        total_branch_qty = sum(b.quantity for b in panel.branch_breakers)
        assert total_branch_qty == 48

        # E.T 수량 확인
        et_items = [a for a in panel.accessories if a.item_name == "E.T"]
        assert len(et_items) == 1
        # 49개 차단기, 100AF → 49 // 6 = 8 (실측 보정: ≤125AF 소형 공식)
        assert et_items[0].quantity == 8

    def test_transform_panel_id_generation(self):
        """
        PanelEstimate ID 생성 확인 (LP-{배치 수량}).
        """
        transformer = DataTransformer()

        placements = [
            MockPlacement(breaker_id="MAIN-1", row=0),
            MockPlacement(breaker_id="BR-1", row=1),
            MockPlacement(breaker_id="BR-2", row=2),
        ]
        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        breakers = [
            MockBreakerInput(id="MAIN-1"),
            MockBreakerInput(id="BR-1"),
            MockBreakerInput(id="BR-2"),
        ]

        estimate_data = transformer.transform(
            placements=placements,
            enclosure_result=enclosure_result,
            breakers=breakers,
            customer_name="ID 테스트",
        )

        panel = estimate_data.panels[0]
        # LP-3 (3개 배치)
        assert panel.panel_id == "LP-3"

    def test_transform_all_items_sorted(self):
        """
        all_items_sorted 속성 확인 (전체 품목 정렬).
        """
        transformer = DataTransformer()

        placements = [
            MockPlacement(breaker_id="MAIN-1", row=0),
            MockPlacement(breaker_id="BR-1", row=1),
        ]
        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        breakers = [MockBreakerInput(id="MAIN-1"), MockBreakerInput(id="BR-1")]

        estimate_data = transformer.transform(
            placements=placements,
            enclosure_result=enclosure_result,
            breakers=breakers,
            customer_name="정렬 테스트",
        )

        panel = estimate_data.panels[0]
        all_items = panel.all_items_sorted

        # 품목 수 확인
        # 외함(1) + 메인(1) + 분기(1) + MAIN BUS-BAR(1) + 부속자재(8+) + 잡자재비(1) + ASSEMBLY CHARGE(1)
        assert len(all_items) > 10

        # 품목 종류 확인
        item_names = [item.item_name for item in all_items]
        # 외함: HDS 모델명 (예: HDS-600*800*200, HB608020)
        has_enclosure = any(
            "HDS" in name or name.startswith("HB") for name in item_names
        )
        assert has_enclosure  # 외함
        # 차단기: MCCB/ELB 또는 모델명 (SBE, SIB, ABN 등)
        has_breaker = any(
            "MCCB" in name or "ELB" in name or name.startswith("S") or name.startswith("AB")
            for name in item_names
        )
        assert has_breaker  # 차단기
        assert "MAIN BUS-BAR" in item_names
        assert "ASSEMBLY CHARGE" in item_names

    def test_transform_empty_project_name(self):
        """
        project_name이 빈 문자열인 경우.
        """
        transformer = DataTransformer()

        placements = [MockPlacement(breaker_id="MAIN-1", row=0)]
        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        breakers = [MockBreakerInput(id="MAIN-1")]

        estimate_data = transformer.transform(
            placements=placements,
            enclosure_result=enclosure_result,
            breakers=breakers,
            customer_name="고객명",
            project_name="",
        )

        assert estimate_data.project_name == ""
        assert estimate_data.customer_name == "고객명"
