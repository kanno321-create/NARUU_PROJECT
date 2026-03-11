"""
Simple TTL memory cache decorator with p95 monitoring.

Phase VII-2: 캐시 모니터링 기능 추가
- 히트/미스 카운팅
- 응답 시간 추적 (p95)
- 메트릭 조회 API

TTL 설정 (CLAUDE.md 기준):
- 카탈로그 캐시: 900s (15분)
- 가격 캐시: 300s (5분)
"""

import logging
import time
from collections import deque
from collections.abc import Callable
from functools import wraps
from typing import Any

from kis_estimator_core.core.ssot.constants import (
    CATALOG_CACHE_TTL,
    METRICS_WINDOW_SIZE,
    PRICE_CACHE_TTL,
)

logger = logging.getLogger(__name__)


class CacheMetrics:
    """캐시 성능 메트릭 수집기"""

    def __init__(self, window_size: int = METRICS_WINDOW_SIZE):
        self.hits = 0
        self.misses = 0
        self.latencies: deque = deque(maxlen=window_size)
        self._window_size = window_size

    def record_hit(self, latency_ms: float):
        """캐시 히트 기록"""
        self.hits += 1
        self.latencies.append(latency_ms)

    def record_miss(self, latency_ms: float):
        """캐시 미스 기록"""
        self.misses += 1
        self.latencies.append(latency_ms)

    @property
    def hit_rate(self) -> float:
        """캐시 히트율 (0.0 ~ 1.0)"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    @property
    def p50_latency_ms(self) -> float:
        """p50 레이턴시 (ms)"""
        return self._percentile(50)

    @property
    def p95_latency_ms(self) -> float:
        """p95 레이턴시 (ms)"""
        return self._percentile(95)

    @property
    def p99_latency_ms(self) -> float:
        """p99 레이턴시 (ms)"""
        return self._percentile(99)

    def _percentile(self, p: int) -> float:
        """특정 백분위수 계산"""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * p / 100)
        idx = min(idx, len(sorted_latencies) - 1)
        return sorted_latencies[idx]

    def get_summary(self) -> dict[str, Any]:
        """메트릭 요약 반환"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": self.hits + self.misses,
            "hit_rate": round(self.hit_rate, 4),
            "p50_ms": round(self.p50_latency_ms, 2),
            "p95_ms": round(self.p95_latency_ms, 2),
            "p99_ms": round(self.p99_latency_ms, 2),
        }

    def reset(self):
        """메트릭 초기화"""
        self.hits = 0
        self.misses = 0
        self.latencies.clear()


class TTLCache:
    """
    Thread-unsafe in-memory TTL cache with monitoring.

    Features:
    - TTL 기반 자동 만료
    - 히트/미스 카운팅
    - p95 레이턴시 추적
    """

    def __init__(self):
        self._cache: dict[tuple[str, tuple], tuple[float, Any]] = {}
        self.metrics = CacheMetrics()

    def get(self, key: tuple[str, tuple]) -> Any:
        """Get value if not expired, else raise KeyError."""
        if key not in self._cache:
            raise KeyError(f"Key {key} not in cache")

        expiry, value = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            raise KeyError(f"Key {key} expired")

        return value

    def set(self, key: tuple[str, tuple], value: Any, ttl: int):
        """Store value with TTL in seconds."""
        expiry = time.time() + ttl
        self._cache[key] = (expiry, value)

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()

    def size(self) -> int:
        """현재 캐시 크기"""
        return len(self._cache)

    def get_metrics(self) -> dict[str, Any]:
        """캐시 메트릭 조회"""
        return {
            "cache_size": self.size(),
            **self.metrics.get_summary(),
        }


# Global cache instance
_GLOBAL_CACHE = TTLCache()


def ttl_cache(ttl: int) -> Callable:
    """
    Decorator for caching function results with TTL and p95 monitoring.

    Args:
        ttl: Time-to-live in seconds

    Returns:
        Decorated function with caching behavior

    Example:
        >>> @ttl_cache(ttl=300)
        ... def expensive_function(arg1, arg2):
        ...     return compute_expensive_result(arg1, arg2)

    Metrics:
        - 히트/미스 카운팅
        - p95 레이턴시 추적
        - cache_metrics() 메서드로 조회
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Create cache key from function name and arguments
            # Note: kwargs not supported in this simple implementation
            if kwargs:
                raise ValueError(
                    f"ttl_cache does not support keyword arguments: {kwargs}"
                )

            cache_key = (func.__name__, args)

            # Try to get from cache
            try:
                result = _GLOBAL_CACHE.get(cache_key)
                # 캐시 히트 - 레이턴시 기록
                latency_ms = (time.time() - start_time) * 1000
                _GLOBAL_CACHE.metrics.record_hit(latency_ms)
                return result
            except KeyError:
                pass

            # Cache miss - compute and store
            result = func(*args, **kwargs)
            _GLOBAL_CACHE.set(cache_key, result, ttl)

            # 캐시 미스 - 레이턴시 기록
            latency_ms = (time.time() - start_time) * 1000
            _GLOBAL_CACHE.metrics.record_miss(latency_ms)

            return result

        # Add cache control methods
        wrapper.cache_clear = _GLOBAL_CACHE.clear  # type: ignore
        wrapper.cache_info = lambda: {  # type: ignore
            "size": len(_GLOBAL_CACHE._cache),
            "ttl": ttl,
        }
        wrapper.cache_metrics = _GLOBAL_CACHE.get_metrics  # type: ignore

        return wrapper

    return decorator


def get_global_cache_metrics() -> dict[str, Any]:
    """전역 캐시 메트릭 조회"""
    return _GLOBAL_CACHE.get_metrics()


def reset_cache_metrics():
    """캐시 메트릭 초기화 (테스트용)"""
    _GLOBAL_CACHE.metrics.reset()
