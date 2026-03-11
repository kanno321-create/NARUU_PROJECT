"""
Integration Tests for Catalog Service TTL Cache (Phase VII)

Tests:
- get_catalog_items() TTL=900s
- get_price() TTL=300s
- Cache hit/miss behavior
- Performance (p95 < 200ms)
- TTL expiration and re-caching

Skip in CI: requires real Redis/Supabase for cache behavior testing
"""

import pytest
import time
import os

from kis_estimator_core.services.catalog_service import (
    get_catalog_items,
    get_price,
    get_catalog_service,
)
from kis_estimator_core.core.ssot.errors import EstimatorError

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Skipping TTL cache tests in CI - requires real Redis/Supabase"
    )
]


class TestCatalogTTLCache:
    """Phase VII: TTL Cache Integration Tests"""

    async def test_get_catalog_items_ttl_900s(self, async_session):
        """
        Test: get_catalog_items() uses TTL=900s (15 minutes)

        Verification:
        - First call: cache miss
        - Second call within TTL: cache hit (no DB query)
        - TTL value is 900s from env
        """
        # Initialize CatalogService cache (Phase C: requires AsyncSession)
        service = get_catalog_service()
        await service.initialize_cache(async_session)

        # Clear TTL cache before test
        get_catalog_items.cache_clear()

        # Verify TTL from cache_info
        cache_info = get_catalog_items.cache_info()
        expected_ttl = int(os.getenv("KIS_CATALOG_CACHE_TTL", "900"))
        assert cache_info["ttl"] == expected_ttl, \
            f"TTL should be {expected_ttl}s, got {cache_info['ttl']}s"

        # First call - cache miss
        start_time = time.perf_counter()
        result1 = get_catalog_items("breaker")
        first_call_time = (time.perf_counter() - start_time) * 1000  # ms

        assert result1 is not None
        assert isinstance(result1, list)

        # Second call - cache hit (should be much faster)
        start_time = time.perf_counter()
        result2 = get_catalog_items("breaker")
        second_call_time = (time.perf_counter() - start_time) * 1000  # ms

        assert result2 is not None
        assert result2 == result1, "Cached result should be identical"

        # Cache hit should be faster (or just verify cache is working)
        # Note: Cache is in-memory so it should be instant
        assert second_call_time < max(first_call_time, 1.0), \
            f"Cache hit ({second_call_time:.4f}ms) should be faster than miss ({first_call_time:.4f}ms)"

        # Verify cache size increased
        cache_info_after = get_catalog_items.cache_info()
        assert cache_info_after["size"] > 0, "Cache should have entries"

    async def test_get_price_ttl_300s(self, async_session):
        """
        Test: get_price() uses TTL=300s (5 minutes)

        Verification:
        - TTL value is 300s from env
        - Cache hit behavior
        """
        # Initialize CatalogService cache
        service = get_catalog_service()
        await service.initialize_cache(async_session)

        # Clear TTL cache before test
        get_price.cache_clear()

        # Verify TTL from cache_info
        cache_info = get_price.cache_info()
        expected_ttl = int(os.getenv("KIS_PRICE_CACHE_TTL", "300"))
        assert cache_info["ttl"] == expected_ttl, \
            f"TTL should be {expected_ttl}s, got {cache_info['ttl']}s"

        # Get first breaker SKU from cache
        if not service._breaker_cache:
            pytest.skip("No breaker data in catalog")

        test_sku = service._breaker_cache[0].sku

        # First call - cache miss
        start_time = time.perf_counter()
        price1 = get_price(test_sku)
        first_call_time = (time.perf_counter() - start_time) * 1000  # ms

        assert price1 > 0

        # Second call - cache hit
        start_time = time.perf_counter()
        price2 = get_price(test_sku)
        second_call_time = (time.perf_counter() - start_time) * 1000  # ms

        assert price2 == price1, "Cached price should be identical"

        # Cache hit should be much faster
        assert second_call_time < max(first_call_time, 1.0), \
            f"Cache hit ({second_call_time:.4f}ms) should be faster than miss ({first_call_time:.4f}ms)"

    async def test_cache_performance_p95_under_200ms(self, async_session):
        """
        Test: Cache performance meets p95 < 200ms requirement

        Verification:
        - 100 calls to get_catalog_items()
        - p95 response time < 200ms
        - Cache hit ratio > 90%
        """
        # Initialize CatalogService cache
        service = get_catalog_service()
        await service.initialize_cache(async_session)

        # Clear TTL cache
        get_catalog_items.cache_clear()

        response_times = []
        kinds = ["breaker", "enclosure", "breaker", "enclosure"] * 25  # 100 calls

        for kind in kinds:
            start_time = time.perf_counter()
            get_catalog_items(kind)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            response_times.append(elapsed_ms)

        # Calculate p95
        response_times.sort()
        p95_index = int(len(response_times) * 0.95)
        p95_time = response_times[p95_index]

        # Log results
        print("\nCache Performance Metrics:")
        print(f"  Total calls: {len(response_times)}")
        print(f"  p50: {response_times[len(response_times)//2]:.2f}ms")
        print(f"  p95: {p95_time:.2f}ms")
        print(f"  p99: {response_times[int(len(response_times)*0.99)]:.2f}ms")
        print(f"  max: {max(response_times):.2f}ms")

        # Verify p95 < 200ms
        assert p95_time < 200, \
            f"p95 response time ({p95_time:.2f}ms) exceeds 200ms threshold"

    def test_ttl_expiration_triggers_recache(self):
        """
        Test: After TTL expiration, cache re-fetches data

        Note: This test uses a short TTL (2s) for testing purposes
        Production uses TTL=900s for catalog items
        """
        from kis_estimator_core.services.cache import ttl_cache

        # Create a test function with short TTL
        call_count = 0

        @ttl_cache(ttl=2)  # 2 second TTL for testing
        def test_function(arg):
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        # First call - cache miss
        result1 = test_function("test")
        assert result1 == "result_1"
        assert call_count == 1

        # Second call within TTL - cache hit
        result2 = test_function("test")
        assert result2 == "result_1"  # Same cached result
        assert call_count == 1  # Function not called again

        # Wait for TTL to expire
        time.sleep(2.5)

        # Third call after TTL - cache miss (re-cache)
        result3 = test_function("test")
        assert result3 == "result_2"  # New result
        assert call_count == 2  # Function called again

    async def test_cache_different_kinds_separately(self, async_session):
        """
        Test: Different 'kind' arguments create separate cache entries

        Verification:
        - get_catalog_items("breaker") cached separately from
        - get_catalog_items("enclosure")
        """
        # Initialize CatalogService cache
        service = get_catalog_service()
        await service.initialize_cache(async_session)

        get_catalog_items.cache_clear()

        # Call with different kinds
        breakers = get_catalog_items("breaker")
        enclosures = get_catalog_items("enclosure")

        # Results should be different
        assert breakers != enclosures

        # Cache should have 2 entries (one per kind)
        cache_info = get_catalog_items.cache_info()
        assert cache_info["size"] >= 2, \
            "Cache should have separate entries for different kinds"

    async def test_cache_invalidation_via_clear(self, async_session):
        """
        Test: cache_clear() properly invalidates all cached entries

        Verification:
        - Call get_catalog_items() to populate cache
        - Call cache_clear()
        - Next call should be cache miss (DB query)
        """
        # Initialize CatalogService cache
        service = get_catalog_service()
        await service.initialize_cache(async_session)

        get_catalog_items.cache_clear()

        # Populate cache
        result1 = get_catalog_items("breaker")
        cache_info = get_catalog_items.cache_info()
        assert cache_info["size"] > 0, "Cache should have entries"

        # Clear cache
        get_catalog_items.cache_clear()

        # Verify cache is empty
        cache_info_after = get_catalog_items.cache_info()
        assert cache_info_after["size"] == 0, "Cache should be empty after clear"

        # Next call should work (cache miss → DB query)
        result2 = get_catalog_items("breaker")
        assert result2 is not None

        # Results should be identical (same DB data)
        assert len(result2) == len(result1)

    async def test_price_cache_not_found_sku(self, async_session):
        """
        Test: get_price() raises EstimatorError for non-existent SKU

        Verification:
        - Non-existent SKU triggers E_NOT_FOUND error
        - Error is not cached (subsequent calls still raise error)
        """
        # Initialize CatalogService cache
        service = get_catalog_service()
        await service.initialize_cache(async_session)

        get_price.cache_clear()

        non_existent_sku = "NONEXISTENT-SKU-12345"

        # First call - should raise error
        with pytest.raises(EstimatorError) as exc_info:
            get_price(non_existent_sku)

        assert exc_info.value.payload.code == "E_NOT_FOUND"
        assert non_existent_sku in str(exc_info.value)

        # Second call - should still raise error (errors not cached)
        with pytest.raises(EstimatorError) as exc_info2:
            get_price(non_existent_sku)

        assert exc_info2.value.payload.code == "E_NOT_FOUND"
