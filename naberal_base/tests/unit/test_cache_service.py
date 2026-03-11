"""
Unit Tests for services/cache.py
Coverage target: >90% for CacheMetrics, TTLCache, and ttl_cache decorator
"""

import time

import pytest

from kis_estimator_core.services.cache import (
    _GLOBAL_CACHE,
    CATALOG_CACHE_TTL,
    PRICE_CACHE_TTL,
    CacheMetrics,
    TTLCache,
    get_global_cache_metrics,
    reset_cache_metrics,
    ttl_cache,
)


class TestCacheMetrics:
    """Tests for CacheMetrics class"""

    def test_initial_state(self):
        """Test initial state of CacheMetrics"""
        metrics = CacheMetrics()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert len(metrics.latencies) == 0

    def test_record_hit(self):
        """Test recording cache hit"""
        metrics = CacheMetrics()
        metrics.record_hit(1.5)
        assert metrics.hits == 1
        assert metrics.misses == 0
        assert 1.5 in metrics.latencies

    def test_record_miss(self):
        """Test recording cache miss"""
        metrics = CacheMetrics()
        metrics.record_miss(2.5)
        assert metrics.hits == 0
        assert metrics.misses == 1
        assert 2.5 in metrics.latencies

    def test_hit_rate_no_requests(self):
        """Test hit rate with no requests"""
        metrics = CacheMetrics()
        assert metrics.hit_rate == 0.0

    def test_hit_rate_all_hits(self):
        """Test hit rate with all hits"""
        metrics = CacheMetrics()
        metrics.record_hit(1.0)
        metrics.record_hit(1.0)
        assert metrics.hit_rate == 1.0

    def test_hit_rate_mixed(self):
        """Test hit rate with mixed hits and misses"""
        metrics = CacheMetrics()
        metrics.record_hit(1.0)
        metrics.record_miss(1.0)
        assert metrics.hit_rate == 0.5

    def test_p50_latency_empty(self):
        """Test p50 latency with no data"""
        metrics = CacheMetrics()
        assert metrics.p50_latency_ms == 0.0

    def test_p50_latency(self):
        """Test p50 latency calculation"""
        metrics = CacheMetrics()
        for i in range(1, 11):
            metrics.record_hit(float(i))
        # Verify p50 is calculated (value depends on implementation)
        assert metrics.p50_latency_ms > 0
        assert 4 <= metrics.p50_latency_ms <= 7

    def test_p95_latency(self):
        """Test p95 latency calculation"""
        metrics = CacheMetrics()
        for i in range(1, 101):
            metrics.record_hit(float(i))
        # Verify p95 is calculated (value depends on implementation)
        assert metrics.p95_latency_ms > 0
        assert 90 <= metrics.p95_latency_ms <= 100

    def test_p99_latency(self):
        """Test p99 latency calculation"""
        metrics = CacheMetrics()
        for i in range(1, 101):
            metrics.record_hit(float(i))
        # Verify p99 is calculated (value depends on implementation)
        assert metrics.p99_latency_ms > 0
        assert 95 <= metrics.p99_latency_ms <= 100

    def test_get_summary(self):
        """Test get_summary returns correct structure"""
        metrics = CacheMetrics()
        metrics.record_hit(1.0)
        metrics.record_miss(2.0)

        summary = metrics.get_summary()
        assert "hits" in summary
        assert "misses" in summary
        assert "total" in summary
        assert "hit_rate" in summary
        assert "p50_ms" in summary
        assert "p95_ms" in summary
        assert "p99_ms" in summary
        assert summary["hits"] == 1
        assert summary["misses"] == 1
        assert summary["total"] == 2

    def test_reset(self):
        """Test reset clears all metrics"""
        metrics = CacheMetrics()
        metrics.record_hit(1.0)
        metrics.record_miss(2.0)

        metrics.reset()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert len(metrics.latencies) == 0

    def test_window_size_limit(self):
        """Test that latencies are limited by window size"""
        metrics = CacheMetrics(window_size=5)
        for i in range(10):
            metrics.record_hit(float(i))
        assert len(metrics.latencies) == 5


class TestTTLCache:
    """Tests for TTLCache class"""

    def test_set_and_get(self):
        """Test basic set and get operations"""
        cache = TTLCache()
        key = ("test_func", (1, 2))
        cache.set(key, "value", ttl=60)
        assert cache.get(key) == "value"

    def test_get_nonexistent_key(self):
        """Test getting non-existent key raises KeyError"""
        cache = TTLCache()
        with pytest.raises(KeyError):
            cache.get(("nonexistent", ()))

    def test_get_expired_key(self):
        """Test getting expired key raises KeyError"""
        cache = TTLCache()
        key = ("test_func", (1,))
        cache.set(key, "value", ttl=0)  # Expires immediately
        time.sleep(0.01)  # Small delay to ensure expiry
        with pytest.raises(KeyError):
            cache.get(key)

    def test_clear(self):
        """Test clear removes all entries"""
        cache = TTLCache()
        cache.set(("a", ()), "a", ttl=60)
        cache.set(("b", ()), "b", ttl=60)
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0

    def test_size(self):
        """Test size returns correct count"""
        cache = TTLCache()
        assert cache.size() == 0

        cache.set(("a", ()), "a", ttl=60)
        assert cache.size() == 1

        cache.set(("b", ()), "b", ttl=60)
        assert cache.size() == 2

    def test_get_metrics(self):
        """Test get_metrics returns correct structure"""
        cache = TTLCache()
        metrics = cache.get_metrics()

        assert "cache_size" in metrics
        assert "hits" in metrics
        assert "misses" in metrics
        assert "hit_rate" in metrics


class TestTTLCacheDecorator:
    """Tests for ttl_cache decorator"""

    def setup_method(self):
        """Clear cache before each test"""
        _GLOBAL_CACHE.clear()
        reset_cache_metrics()

    def test_decorator_caches_result(self):
        """Test that decorator caches function result"""
        call_count = 0

        @ttl_cache(ttl=60)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - should execute function
        result1 = expensive_func(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - should return cached result
        result2 = expensive_func(5)
        assert result2 == 10
        assert call_count == 1  # Function not called again

    def test_decorator_different_args(self):
        """Test that different args create different cache entries"""
        call_count = 0

        @ttl_cache(ttl=60)
        def add_one(x):
            nonlocal call_count
            call_count += 1
            return x + 1

        result1 = add_one(1)
        result2 = add_one(2)
        result3 = add_one(1)  # Cached

        assert result1 == 2
        assert result2 == 3
        assert result3 == 2
        assert call_count == 2  # Only 2 unique calls

    def test_decorator_kwargs_raises(self):
        """Test that kwargs raise ValueError"""
        @ttl_cache(ttl=60)
        def func_with_kwargs(x, y=1):
            return x + y

        with pytest.raises(ValueError) as exc:
            func_with_kwargs(1, y=2)
        assert "keyword arguments" in str(exc.value)

    def test_decorator_cache_clear(self):
        """Test cache_clear method"""
        @ttl_cache(ttl=60)
        def cached_func(x):
            return x

        cached_func(1)
        cached_func.cache_clear()
        assert _GLOBAL_CACHE.size() == 0

    def test_decorator_cache_info(self):
        """Test cache_info method"""
        @ttl_cache(ttl=300)
        def cached_func(x):
            return x

        info = cached_func.cache_info()
        assert "size" in info
        assert "ttl" in info
        assert info["ttl"] == 300

    def test_decorator_cache_metrics(self):
        """Test cache_metrics method"""
        @ttl_cache(ttl=60)
        def cached_func(x):
            return x

        cached_func(1)
        cached_func(1)  # Hit

        metrics = cached_func.cache_metrics()
        assert "hits" in metrics
        assert "misses" in metrics


class TestGlobalCacheFunctions:
    """Tests for global cache functions"""

    def setup_method(self):
        """Clear cache before each test"""
        _GLOBAL_CACHE.clear()
        reset_cache_metrics()

    def test_get_global_cache_metrics(self):
        """Test get_global_cache_metrics returns correct structure"""
        metrics = get_global_cache_metrics()
        assert "cache_size" in metrics
        assert "hits" in metrics
        assert "misses" in metrics

    def test_reset_cache_metrics(self):
        """Test reset_cache_metrics clears metrics"""
        _GLOBAL_CACHE.metrics.record_hit(1.0)
        _GLOBAL_CACHE.metrics.record_miss(2.0)

        reset_cache_metrics()
        assert _GLOBAL_CACHE.metrics.hits == 0
        assert _GLOBAL_CACHE.metrics.misses == 0


class TestCacheConstants:
    """Tests for cache constants"""

    def test_catalog_cache_ttl(self):
        """Test CATALOG_CACHE_TTL is 900 seconds (15 minutes)"""
        assert CATALOG_CACHE_TTL == 900

    def test_price_cache_ttl(self):
        """Test PRICE_CACHE_TTL is 300 seconds (5 minutes)"""
        assert PRICE_CACHE_TTL == 300
