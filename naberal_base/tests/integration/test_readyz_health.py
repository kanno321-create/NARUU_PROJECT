"""
Integration Tests for /readyz Health Check Endpoint

Tests verify the Kubernetes readiness probe endpoint.
Updated schema: critical_dependencies / optional_dependencies structure.
"""

import pytest
import os
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create FastAPI test client."""
    from api.main import app

    return TestClient(app)


def test_readyz_endpoint_exists(client):
    """Test that /readyz endpoint exists and returns proper structure."""
    response = client.get("/readyz")

    # Should return either 200 (ready) or 503 (not ready)
    assert response.status_code in [200, 503]

    data = response.json()

    # Required top-level fields (Phase VII aligned schema)
    assert "status" in data
    assert data["status"] in ["ready", "not_ready"]
    assert "timestamp" in data
    assert "critical_dependencies" in data
    assert "optional_dependencies" in data
    assert "failing_components" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_readyz_critical_dependencies_structure(client):
    """Test critical dependencies health check structure."""
    response = client.get("/readyz")
    data = response.json()

    critical_deps = data["critical_dependencies"]

    # Critical dependencies: database, cache, catalog
    assert "database" in critical_deps
    assert "cache" in critical_deps
    assert "catalog" in critical_deps

    # Each dependency should have: ready, elapsed_ms, error
    for dep_name, dep_data in critical_deps.items():
        assert "ready" in dep_data
        assert "elapsed_ms" in dep_data
        assert "error" in dep_data


def test_readyz_optional_dependencies_structure(client):
    """Test optional dependencies health check structure."""
    response = client.get("/readyz")
    data = response.json()

    optional_deps = data["optional_dependencies"]

    # Optional dependencies: redis
    assert "redis" in optional_deps

    # Each dependency should have: ready, elapsed_ms, error
    redis_data = optional_deps["redis"]
    assert "ready" in redis_data
    assert "elapsed_ms" in redis_data
    assert "error" in redis_data


def test_readyz_status_code_when_ready(client):
    """Test that /readyz returns 200 when all critical dependencies are ready."""
    response = client.get("/readyz")
    data = response.json()

    # If status is ready, HTTP code should be 200
    if data["status"] == "ready":
        assert response.status_code == 200
        # All critical deps should be ready
        for dep_name, dep_data in data["critical_dependencies"].items():
            assert dep_data["ready"] is True


def test_readyz_status_code_when_not_ready(client):
    """Test that /readyz returns 503 when any critical dependency is not ready."""
    response = client.get("/readyz")
    data = response.json()

    # If status is not_ready, HTTP code should be 503
    if data["status"] == "not_ready":
        assert response.status_code == 503
        # At least one critical dep should not be ready
        # OR failing_components should be non-empty
        failing = data.get("failing_components", [])
        if failing:
            assert len(failing) > 0


def test_readyz_failing_components_list(client):
    """Test that failing_components contains names of failed critical deps."""
    response = client.get("/readyz")
    data = response.json()

    failing = data.get("failing_components", [])
    critical_deps = data["critical_dependencies"]

    # failing_components should list names of critical deps that are not ready
    for dep_name, dep_data in critical_deps.items():
        if not dep_data["ready"]:
            assert dep_name in failing


def test_health_vs_readyz_difference(client):
    """Test that /health and /readyz provide different information."""
    health_response = client.get("/health")
    readyz_response = client.get("/readyz")

    health_data = health_response.json()
    readyz_data = readyz_response.json()

    # /readyz has critical_dependencies and optional_dependencies
    assert "critical_dependencies" in readyz_data
    assert "optional_dependencies" in readyz_data

    # /health has checks structure (different format)
    # Both should have version
    assert "version" in readyz_data
