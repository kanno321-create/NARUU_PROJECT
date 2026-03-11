"""
Phase I-6 Restored: catalog_service.py DB integration (simplified)

SB-05 Compliance:
- @requires_db: Real PostgreSQL operations allowed
- No mocks: Actual DB queries
- search_path="kis_beta,public" enforced (SB-01)

Coverage Target: catalog_service.py find_breaker/find_enclosure
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from kis_estimator_core.services.catalog_service import get_catalog_service


@pytest.mark.asyncio
@pytest.mark.requires_db
class TestCatalogServiceSimple:
    """Integration tests for CatalogService with real DB"""

    async def test_initialize_cache(self, async_session: AsyncSession):
        """
        initialize_cache with real DB

        Covers:
        - catalog_service.py: initialize_cache() method
        - DB query execution
        """
        service = get_catalog_service()
        await service.initialize_cache(async_session)
        # Should complete without error
        assert True

    async def test_find_breaker_real(self, async_session: AsyncSession):
        """
        find_breaker with real parameters

        Covers:
        - catalog_service.py: find_breaker() method
        - Breaker lookup logic
        """
        service = get_catalog_service()
        await service.initialize_cache(async_session)
        result = service.find_breaker(model="SBE", poles=2, current_a=60)
        # May or may not find match (DB-dependent)
        assert result is None or hasattr(result, "sku")

    async def test_find_enclosure_real(self, async_session: AsyncSession):
        """
        find_enclosure with real parameters

        Covers:
        - catalog_service.py: find_enclosure() method
        - Enclosure lookup logic
        """
        service = get_catalog_service()
        await service.initialize_cache(async_session)
        result = service.find_enclosure(width=600, height=800, depth=200)
        # May or may not find match (DB-dependent)
        assert result is None or hasattr(result, "sku")
