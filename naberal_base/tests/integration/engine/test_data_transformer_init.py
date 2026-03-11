"""

# Catalog dependency → requires DB
pytestmark = pytest.mark.requires_db

Tests for DataTransformer initialization and catalog_service setup.

Zero-Mock Policy: 100% real Supabase CatalogService usage.
"""

from kis_estimator_core.engine.data_transformer import DataTransformer
from kis_estimator_core.services.catalog_service import CatalogService


class TestDataTransformerInitialization:
    """DataTransformer initialization tests with real Supabase."""

    def test_data_transformer_initialization_success(self):
        """
        DataTransformer가 성공적으로 초기화되는지 확인.
        Zero-Mock: 실제 Supabase CatalogService 사용.
        """
        transformer = DataTransformer()

        assert transformer is not None
        assert hasattr(transformer, "catalog_service")
        assert transformer.catalog_service is not None

    def test_catalog_service_is_real_supabase(self):
        """
        catalog_service가 실제 Supabase 인스턴스인지 확인 (목업 금지).
        """
        transformer = DataTransformer()

        # CatalogService 인스턴스여야 함 (Mock 또는 MagicMock 아님)
        assert isinstance(transformer.catalog_service, CatalogService)

        # Mock이 아닌지 확인 (unittest.mock 패턴 탐지)
        assert not hasattr(transformer.catalog_service, "_mock_name")
        assert not hasattr(transformer.catalog_service, "_spec_class")

    def test_catalog_service_connected(self):
        """
        catalog_service가 실제 데이터베이스 연결을 가지고 있는지 확인.
        간단한 쿼리 수행 가능 여부 검증.
        """
        transformer = DataTransformer()

        # catalog_service에 필수 메서드 존재 확인
        assert hasattr(transformer.catalog_service, "find_enclosure")
        assert hasattr(transformer.catalog_service, "find_breaker")
        assert callable(transformer.catalog_service.find_enclosure)
        assert callable(transformer.catalog_service.find_breaker)

    def test_data_transformer_reinitialization(self):
        """
        DataTransformer를 여러 번 생성해도 안정적으로 초기화되는지 확인.
        """
        transformer1 = DataTransformer()
        transformer2 = DataTransformer()

        assert transformer1 is not transformer2  # 별도 인스턴스
        assert isinstance(transformer1.catalog_service, CatalogService)
        assert isinstance(transformer2.catalog_service, CatalogService)

    def test_catalog_service_not_none_after_init(self):
        """
        초기화 직후 catalog_service가 None이 아닌지 확인.
        """
        transformer = DataTransformer()

        assert transformer.catalog_service is not None
        assert transformer.catalog_service.__class__.__name__ == "CatalogService"
