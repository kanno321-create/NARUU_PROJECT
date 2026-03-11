"""

# Catalog dependency → requires DB
pytestmark = pytest.mark.requires_db

Tests for DataTransformer._group_breakers method.

Zero-Mock Policy: Uses simple mock placements (no external dependencies).
"""

from kis_estimator_core.engine.data_transformer import DataTransformer


class MockPlacement:
    """Mock placement object for testing."""

    def __init__(self, breaker_id: str, row: int = None):
        self.breaker_id = breaker_id
        if row is not None:
            self.position = {"row": row}
        else:
            # position 자체가 없는 경우
            pass


class TestDataTransformerGroupBreakers:
    """_group_breakers method tests."""

    def test_group_breakers_single_main(self):
        """
        메인 차단기만 있는 경우 (row=0).
        """
        transformer = DataTransformer()

        placements = [
            MockPlacement("MAIN-1", row=0),
        ]

        main, branch = transformer._group_breakers(placements)

        assert len(main) == 1
        assert len(branch) == 0
        assert main[0].breaker_id == "MAIN-1"

    def test_group_breakers_single_branch(self):
        """
        분기 차단기만 있는 경우 (row!=0).
        """
        transformer = DataTransformer()

        placements = [
            MockPlacement("BRANCH-1", row=1),
        ]

        main, branch = transformer._group_breakers(placements)

        assert len(main) == 0
        assert len(branch) == 1
        assert branch[0].breaker_id == "BRANCH-1"

    def test_group_breakers_mixed(self):
        """
        메인 1개 + 분기 3개 혼합 케이스.
        """
        transformer = DataTransformer()

        placements = [
            MockPlacement("MAIN-1", row=0),
            MockPlacement("BRANCH-1", row=1),
            MockPlacement("BRANCH-2", row=2),
            MockPlacement("BRANCH-3", row=3),
        ]

        main, branch = transformer._group_breakers(placements)

        assert len(main) == 1
        assert len(branch) == 3
        assert main[0].breaker_id == "MAIN-1"
        assert branch[0].breaker_id == "BRANCH-1"
        assert branch[1].breaker_id == "BRANCH-2"
        assert branch[2].breaker_id == "BRANCH-3"

    def test_group_breakers_no_position_attribute(self):
        """
        position 속성이 없는 placement → branch_breakers에 추가 (기본값 row=-1).
        """
        transformer = DataTransformer()

        placements = [
            MockPlacement("NO-POS-1"),  # position 속성 없음
        ]

        main, branch = transformer._group_breakers(placements)

        assert len(main) == 0
        assert len(branch) == 1
        assert branch[0].breaker_id == "NO-POS-1"

    def test_group_breakers_position_without_row_key(self):
        """
        position은 있지만 'row' 키가 없는 경우 → branch_breakers에 추가.
        """
        transformer = DataTransformer()

        # position에 row 키 없음
        placement = MockPlacement("NO-ROW-1")
        placement.position = {"col": 5}  # row 키 없음

        placements = [placement]

        main, branch = transformer._group_breakers(placements)

        assert len(main) == 0
        assert len(branch) == 1

    def test_group_breakers_multiple_mains(self):
        """
        여러 개의 메인 차단기 (row=0).
        일반적으로 1개지만, 로직상 여러 개도 처리 가능해야 함.
        """
        transformer = DataTransformer()

        placements = [
            MockPlacement("MAIN-1", row=0),
            MockPlacement("MAIN-2", row=0),
            MockPlacement("BRANCH-1", row=1),
        ]

        main, branch = transformer._group_breakers(placements)

        assert len(main) == 2
        assert len(branch) == 1
        assert main[0].breaker_id == "MAIN-1"
        assert main[1].breaker_id == "MAIN-2"

    def test_group_breakers_empty_list(self):
        """
        빈 placements 리스트 → 빈 결과 반환.
        """
        transformer = DataTransformer()

        placements = []

        main, branch = transformer._group_breakers(placements)

        assert len(main) == 0
        assert len(branch) == 0

    def test_group_breakers_row_negative(self):
        """
        row가 음수인 경우 → branch_breakers에 추가.
        """
        transformer = DataTransformer()

        placements = [
            MockPlacement("NEG-1", row=-5),
        ]

        main, branch = transformer._group_breakers(placements)

        assert len(main) == 0
        assert len(branch) == 1
        assert branch[0].breaker_id == "NEG-1"

    def test_group_breakers_large_row_number(self):
        """
        매우 큰 row 번호 → branch_breakers에 추가.
        """
        transformer = DataTransformer()

        placements = [
            MockPlacement("LARGE-1", row=999),
        ]

        main, branch = transformer._group_breakers(placements)

        assert len(main) == 0
        assert len(branch) == 1
        assert branch[0].breaker_id == "LARGE-1"
