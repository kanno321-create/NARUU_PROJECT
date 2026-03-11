"""
Unit Tests for infra/redis_driver.py
Coverage target: >70% for RedisDriver class

Zero-Mock exception: Unit tests may use unittest.mock for external Redis calls
to avoid requiring real Redis connection in CI environment.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestRedisDriverInit:
    """Tests for RedisDriver initialization"""

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_init_default_params(self, mock_redis_class):
        """Test initialization with default parameters"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()

        mock_redis_class.assert_called_once_with(
            host="localhost",
            port=6379,
            db=0,
            password=None,
            decode_responses=True,
        )
        assert driver.client == mock_client

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_init_custom_params(self, mock_redis_class):
        """Test initialization with custom parameters"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client

        driver = RedisDriver(
            host="redis.example.com", port=6380, db=1, password="secret"
        )

        mock_redis_class.assert_called_once_with(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            decode_responses=True,
        )


class TestRedisDriverPing:
    """Tests for RedisDriver ping method"""

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_ping_success(self, mock_redis_class):
        """Test ping returns True on success"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.ping()

        assert result is True
        mock_client.ping.assert_called_once()

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_ping_failure(self, mock_redis_class):
        """Test ping returns False on failure"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.ping.side_effect = Exception("Connection refused")
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.ping()

        assert result is False


class TestRedisDriverHealthCheck:
    """Tests for RedisDriver health_check method"""

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_health_check_connected(self, mock_redis_class):
        """Test health check returns connected status"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.info.return_value = {
            "used_memory_human": "1.5M",
            "connected_clients": 10,
        }
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.health_check()

        assert result["status"] == "connected"
        assert result["connected"] is True
        assert result["used_memory"] == "1.5M"
        assert result["connected_clients"] == 10

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_health_check_disconnected(self, mock_redis_class):
        """Test health check returns disconnected status"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.ping.return_value = False
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.health_check()

        assert result["status"] == "disconnected"
        assert result["connected"] is False

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_health_check_error(self, mock_redis_class):
        """Test health check returns error status on exception during info()"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        # ping succeeds but info() raises exception
        mock_client.ping.return_value = True
        mock_client.info.side_effect = Exception("Redis error during info")
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.health_check()

        assert result["status"] == "error"
        assert result["connected"] is False
        assert "error" in result


class TestRedisDriverRateLimit:
    """Tests for RedisDriver rate limit methods"""

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_check_rate_limit_first_request(self, mock_redis_class):
        """Test rate limit allows first request"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.get.return_value = None  # First request
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.check_rate_limit("user:123", rate=100, burst=300, window=60)

        assert result is True
        mock_client.setex.assert_called_once()

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_check_rate_limit_with_tokens(self, mock_redis_class):
        """Test rate limit allows request when tokens available"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.get.return_value = "50"  # 50 tokens available
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.check_rate_limit("user:123", rate=100, burst=300, window=60)

        assert result is True
        mock_client.setex.assert_called()

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_check_rate_limit_no_tokens(self, mock_redis_class):
        """Test rate limit blocks request when tokens below threshold after refill"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        # Use negative value so that after refill (+ rate/window = 1.67), it's still < 1
        mock_client.get.return_value = "-1"  # After refill: -1 + 1.67 = 0.67 < 1
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.check_rate_limit("user:123", rate=100, burst=300, window=60)

        assert result is False

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_check_rate_limit_key_format(self, mock_redis_class):
        """Test rate limit uses correct key format"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.get.return_value = "10"
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        driver.check_rate_limit("user:123")

        mock_client.get.assert_called_with("rl:estimate:user:123")


class TestRedisDriverIdempotency:
    """Tests for RedisDriver idempotency methods"""

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_get_idempotency_key(self, mock_redis_class):
        """Test get_idempotency_key generates consistent hash"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()

        payload = {"customer": "test", "amount": 1000}
        key1 = driver.get_idempotency_key(payload)
        key2 = driver.get_idempotency_key(payload)

        # Same payload should generate same key
        assert key1 == key2
        # Key should be SHA256 hash (64 chars)
        assert len(key1) == 64

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_get_idempotency_key_different_payloads(self, mock_redis_class):
        """Test different payloads generate different keys"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()

        payload1 = {"customer": "test1"}
        payload2 = {"customer": "test2"}

        key1 = driver.get_idempotency_key(payload1)
        key2 = driver.get_idempotency_key(payload2)

        assert key1 != key2

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_check_idempotency_new_request(self, mock_redis_class):
        """Test check_idempotency returns None for new request"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.check_idempotency("hash123")

        assert result is None
        mock_client.get.assert_called_with("idem:estimate:hash123")

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_check_idempotency_existing_request(self, mock_redis_class):
        """Test check_idempotency returns result_id for existing request"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.get.return_value = "EST-123"
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.check_idempotency("hash123")

        assert result == "EST-123"

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_set_idempotency(self, mock_redis_class):
        """Test set_idempotency stores result with TTL"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        driver.set_idempotency("hash123", "EST-456", ttl=3600)

        mock_client.setex.assert_called_with("idem:estimate:hash123", 3600, "EST-456")

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_set_idempotency_default_ttl(self, mock_redis_class):
        """Test set_idempotency uses default TTL (24h)"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        driver.set_idempotency("hash123", "EST-456")

        # Default TTL is 86400 (24 hours)
        mock_client.setex.assert_called_with("idem:estimate:hash123", 86400, "EST-456")


class TestRedisDriverProbeNamespaces:
    """Tests for RedisDriver probe_namespaces method"""

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_probe_namespaces_success(self, mock_redis_class):
        """Test probe_namespaces returns key counts"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.keys.side_effect = [
            ["rl:estimate:1", "rl:estimate:2"],  # rate limit keys
            ["idem:estimate:a"],  # idempotency keys
        ]
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.probe_namespaces()

        assert result["rate_limit_keys"] == 2
        assert result["idempotency_keys"] == 1

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_probe_namespaces_error(self, mock_redis_class):
        """Test probe_namespaces returns zeros on error"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.keys.side_effect = Exception("Redis error")
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.probe_namespaces()

        assert result["rate_limit_keys"] == 0
        assert result["idempotency_keys"] == 0

    @patch("kis_estimator_core.infra.redis_driver.redis.Redis")
    def test_probe_namespaces_empty(self, mock_redis_class):
        """Test probe_namespaces returns zeros when no keys"""
        from kis_estimator_core.infra.redis_driver import RedisDriver

        mock_client = MagicMock()
        mock_client.keys.return_value = []
        mock_redis_class.return_value = mock_client

        driver = RedisDriver()
        result = driver.probe_namespaces()

        assert result["rate_limit_keys"] == 0
        assert result["idempotency_keys"] == 0
