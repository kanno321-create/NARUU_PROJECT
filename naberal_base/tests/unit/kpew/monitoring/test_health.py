"""
Unit Tests: kpew/monitoring/health.py
"""

import pytest
from unittest.mock import Mock
from kis_estimator_core.kpew.monitoring.health import (
    check_kpew_health_async,
    _check_database_async,
    _check_llm_api,
    _check_quality_gates,
)

pytestmark = pytest.mark.unit


class TestCheckKpewHealthAsync:
    @pytest.mark.asyncio
    async def test_all_healthy(self, monkeypatch):
        async def mock_db():
            return {"status": "ok", "latency_ms": 50, "timezone_utc": True, "error": None}
        def mock_llm():
            return {"status": "ok", "provider": "claude", "error": None}
        def mock_gates():
            return {"status": "ok", "config_hash": "abc12345", "error": None}

        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_database_async", mock_db)
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_llm_api", mock_llm)
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_quality_gates", mock_gates)

        result = await check_kpew_health_async()
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_db_error(self, monkeypatch):
        async def mock_db():
            return {"status": "error", "latency_ms": 0, "error": "Timeout"}
        def mock_llm():
            return {"status": "ok", "provider": "claude", "error": None}
        def mock_gates():
            return {"status": "ok", "config_hash": "abc", "error": None}

        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_database_async", mock_db)
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_llm_api", mock_llm)
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_quality_gates", mock_gates)

        result = await check_kpew_health_async()
        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_gates_error(self, monkeypatch):
        async def mock_db():
            return {"status": "ok", "latency_ms": 50, "timezone_utc": True, "error": None}
        def mock_llm():
            return {"status": "ok", "provider": "claude", "error": None}
        def mock_gates():
            return {"status": "error", "config_hash": None, "error": "Not found"}

        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_database_async", mock_db)
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_llm_api", mock_llm)
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_quality_gates", mock_gates)

        result = await check_kpew_health_async()
        assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_llm_error(self, monkeypatch):
        async def mock_db():
            return {"status": "ok", "latency_ms": 50, "timezone_utc": True, "error": None}
        def mock_llm():
            return {"status": "error", "provider": "claude", "error": "API error"}
        def mock_gates():
            return {"status": "ok", "config_hash": "abc", "error": None}

        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_database_async", mock_db)
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_llm_api", mock_llm)
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health._check_quality_gates", mock_gates)

        result = await check_kpew_health_async()
        assert result["status"] == "degraded"


class TestCheckDatabaseAsync:
    @pytest.mark.asyncio
    async def test_database_ok(self, monkeypatch):
        async def mock_check_db_health():
            return {"connected": True, "status": "healthy", "timezone_utc": True}

        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health.check_database_health", mock_check_db_health)
        result = await _check_database_async()
        assert result["status"] == "ok"
        assert result["latency_ms"] >= 0
        assert result["timezone_utc"] is True

    @pytest.mark.asyncio
    async def test_database_disconnected(self, monkeypatch):
        async def mock_check_db_health():
            return {"connected": False, "status": "error", "error": "Connection refused"}

        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health.check_database_health", mock_check_db_health)
        result = await _check_database_async()
        assert result["status"] == "error"
        assert "Connection refused" in result["error"]

    @pytest.mark.asyncio
    async def test_database_exception(self, monkeypatch):
        async def mock_check_db_health():
            raise Exception("Network timeout")

        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health.check_database_health", mock_check_db_health)
        result = await _check_database_async()
        assert result["status"] == "error"
        assert "Network timeout" in result["error"]


class TestCheckLlmApi:
    def test_no_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = _check_llm_api()
        assert result["status"] == "error"

    def test_api_success(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="ok")]
        mock_client.messages.create.return_value = mock_response
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health.anthropic.Anthropic", lambda api_key: mock_client)
        result = _check_llm_api()
        assert result["status"] == "ok"

    def test_api_error(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        def mock_client_init(api_key):
            mock_client = Mock()
            mock_client.messages.create.side_effect = Exception("Error")
            return mock_client
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health.anthropic.Anthropic", mock_client_init)
        result = _check_llm_api()
        assert result["status"] == "error"

    def test_api_empty_response(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health.anthropic.Anthropic", lambda api_key: mock_client)
        result = _check_llm_api()
        assert result["status"] == "error"


class TestCheckQualityGates:
    def test_config_not_found(self, monkeypatch):
        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health.os.path.exists", lambda path: False)
        result = _check_quality_gates()
        assert result["status"] == "error"
        assert result["config_hash"] is None

    def test_config_valid(self, monkeypatch):
        def mock_exists(path):
            return True

        def mock_open_func(file, mode='r', encoding=None):
            from io import StringIO
            content = """rules:
  - rule1
balance_limit: 0.04
fit_score_min: 0.90"""
            return StringIO(content)

        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health.os.path.exists", mock_exists)
        monkeypatch.setattr("builtins.open", mock_open_func)
        result = _check_quality_gates()
        assert result["status"] == "ok"
        assert result["config_hash"] is not None

    def test_config_missing_required_key(self, monkeypatch):
        def mock_exists(path):
            return True

        def mock_open_func(file, mode='r', encoding=None):
            from io import StringIO
            content = """rules:
  - rule1
balance_limit: 0.04"""
            return StringIO(content)

        monkeypatch.setattr("kis_estimator_core.kpew.monitoring.health.os.path.exists", mock_exists)
        monkeypatch.setattr("builtins.open", mock_open_func)
        result = _check_quality_gates()
        assert result["status"] == "error"
        assert "fit_score_min" in result["error"]
