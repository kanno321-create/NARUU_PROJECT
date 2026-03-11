"""
Redis Cache Module
Upstash Redis integration for high-performance caching
"""

import json
import redis
from typing import Optional, Any
from api.config import config


class RedisCache:
    """Redis cache client with automatic fallback"""

    def __init__(self):
        """Initialize Redis connection"""
        self.client: Optional[redis.Redis] = None
        self.enabled = False

        if config.REDIS_URL:
            try:
                self.client = redis.from_url(
                    config.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self.client.ping()
                self.enabled = True
                print(f"[OK] Redis connected: {config.REDIS_URL[:50]}...")
            except Exception as e:
                print(f"[WARN] Redis connection failed: {e}")
                print("       Continuing without cache (degraded performance)")
                self.client = None
                self.enabled = False
        else:
            print("[INFO] Redis not configured (REDIS_URL missing)")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"[WARN] Redis GET error for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        if not self.enabled or not self.client:
            return False

        try:
            ttl = ttl or config.REDIS_TTL
            serialized = json.dumps(value, ensure_ascii=False)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"[WARN] Redis SET error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled or not self.client:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"[WARN] Redis DELETE error for key '{key}': {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.enabled or not self.client:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"[WARN] Redis CLEAR error for pattern '{pattern}': {e}")
            return 0

    def health_check(self) -> dict:
        """Check Redis health status"""
        if not self.enabled or not self.client:
            return {
                "status": "disabled",
                "message": "Redis not configured or connection failed",
            }

        try:
            self.client.ping()
            info = self.client.info("memory")
            return {
                "status": "healthy",
                "connected": True,
                "memory_used_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "memory_peak_mb": round(
                    info.get("used_memory_peak", 0) / 1024 / 1024, 2
                ),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
            }


# Global cache instance
cache = RedisCache()
