"""API probe contract tests for Phase VII health endpoints."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json


# ============================================================================
# Evidence Writer Helper Class (방법 3)
# ============================================================================


class EvidenceWriter:
    """Centralized evidence file management with idempotent initialization."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    def initialize(self):
        """Initialize evidence file (idempotent - safe to call multiple times)."""
        if not self._initialized:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write("# API Probe Contract Evidence - Phase VII\n\n")
            self._initialized = True

    def append_section(self, title: str, content: str):
        """Append evidence section to file."""
        self.initialize()  # Always ensure file is initialized
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(f"## {title}\n\n")
            f.write(content)
            f.write("\n")


# ============================================================================
# Session-scoped Fixture (방법 1)
# ============================================================================


@pytest.fixture(scope="session")
def evidence_writer():
    """Provide evidence writer for all tests (session-scoped)."""
    writer = EvidenceWriter(Path("out/evidence/probes/contract.md"))
    writer.initialize()  # Initialize once for entire session
    return writer


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def client():
    """Create FastAPI test client."""
    from api.main import app

    return TestClient(app)


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv("KIS_DISABLE_DB_FEATURES", "1")
    monkeypatch.setenv("APP_ENV", "test")


# ============================================================================
# Contract Tests
# ============================================================================


def test_health_endpoint_contract(client, evidence_writer):
    """
    Test /health endpoint returns correct structure.

    Contract (Phase VII-4 정석):
        - Status: 200 OK (liveness only, no dependency checks)
        - Body: {
            "status": "live",
            "version": str,
            "environment": str
        }

    Note: /health is liveness-only. Use /readyz for readiness with dependencies.
    """
    response = client.get("/health")

    # Status code should be 200 (liveness always OK if process alive)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    body = response.json()

    # Required fields (liveness contract)
    assert "status" in body, "Missing 'status' field"
    assert "version" in body, "Missing 'version' field"
    assert "environment" in body, "Missing 'environment' field"

    # Status field validation (liveness = "live")
    assert body["status"] == "live", f"Expected status='live', got '{body['status']}'"

    # Version format
    assert isinstance(body["version"], str), "Version should be string"
    assert len(body["version"]) > 0, "Version should not be empty"

    # Environment format
    assert isinstance(body["environment"], str), "Environment should be string"

    # Write evidence
    evidence_content = f"""**Status Code**: {response.status_code}

**Response Body**:
```json
{json.dumps(body, indent=2, ensure_ascii=False)}
```

**Contract Validation**: ✅ PASS (Phase VII-4 Liveness Contract)
- ✅ Status field = 'live'
- ✅ Version field present and non-empty
- ✅ Environment field present
"""
    evidence_writer.append_section("/health Endpoint (Liveness)", evidence_content)


def test_health_live_endpoint_contract(client, evidence_writer):
    """
    Test /health/live endpoint returns correct structure.

    Contract:
        - Status: 200 OK (always)
        - Body: {"status": "live"}
    """
    response = client.get("/health/live")

    # Should always be 200 OK
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    body = response.json()

    # Required field
    assert "status" in body, "Missing 'status' field"
    assert body["status"] == "live", f"Expected status='live', got '{body['status']}'"

    # Write evidence
    evidence_content = f"""**Status Code**: {response.status_code}

**Response Body**:
```json
{json.dumps(body, indent=2, ensure_ascii=False)}
```

**Contract Validation**: ✅ PASS
- ✅ Always returns 200 OK
- ✅ Status field is 'live'
"""
    evidence_writer.append_section("/health/live Endpoint", evidence_content)


def test_health_db_endpoint_contract(client, evidence_writer):
    """
    Test /health/db endpoint returns correct structure.

    Contract:
        - Status: 200 OK (DB connected) or 503 (DB disconnected)
        - Body (200): {"status": "connected", "latency_ms": <float>}
        - Body (503): {"status": "disconnected", "error": "<message>"}
    """
    response = client.get("/health/db")

    # Status code should be 200 or 503
    assert response.status_code in [
        200,
        503,
    ], f"Expected 200 or 503, got {response.status_code}"

    body = response.json()

    # Required field
    assert "status" in body, "Missing 'status' field"

    if response.status_code == 200:
        # Connected case
        assert (
            body["status"] == "connected"
        ), f"Expected status='connected' for 200, got '{body['status']}'"
        assert "latency_ms" in body, "Missing 'latency_ms' field"
        assert isinstance(
            body["latency_ms"], (int, float)
        ), "latency_ms should be numeric"
        validation_items = """- ✅ Returns 200 OK when DB connected
- ✅ Status field is 'connected'
- ✅ Latency_ms field present and numeric"""
    else:
        # Disconnected case (503)
        assert (
            body["status"] == "disconnected"
        ), f"Expected status='disconnected' for 503, got '{body['status']}'"
        assert "error" in body, "Missing 'error' field"
        assert isinstance(body["error"], str), "error should be string"
        validation_items = """- ✅ Returns 503 when DB disconnected
- ✅ Status field is 'disconnected'
- ✅ Error field present and descriptive"""

    # Write evidence
    evidence_content = f"""**Status Code**: {response.status_code}

**Response Body**:
```json
{json.dumps(body, indent=2, ensure_ascii=False)}
```

**Contract Validation**: ✅ PASS
{validation_items}
"""
    evidence_writer.append_section("/health/db Endpoint", evidence_content)


def test_health_endpoints_response_time(client, evidence_writer):
    """
    Test that health endpoints respond quickly.

    Expected: All health endpoints < 1000ms
    """
    import time

    endpoints = ["/health", "/health/live", "/health/db"]
    timings = {}

    for endpoint in endpoints:
        start = time.perf_counter()
        response = client.get(endpoint)
        duration_ms = (time.perf_counter() - start) * 1000

        timings[endpoint] = {"duration_ms": duration_ms, "status": response.status_code}

        # Health endpoints should be fast
        assert (
            duration_ms < 1000
        ), f"{endpoint} took {duration_ms:.2f}ms (expected < 1000ms)"

    # Write evidence
    timing_lines = "\n".join(
        f"**{endpoint}**: {timing['duration_ms']:.2f}ms (status: {timing['status']})"
        for endpoint, timing in timings.items()
    )
    evidence_content = f"""{timing_lines}

**Performance Validation**: ✅ PASS
- ✅ All endpoints respond < 1000ms
"""
    evidence_writer.append_section("Response Time Validation", evidence_content)


def test_health_schema_consistency(client, evidence_writer):
    """
    Test that health endpoint schemas are consistent over multiple calls.

    Evidence: 3 consecutive calls return same schema structure.
    """
    responses = []

    for _ in range(3):
        response = client.get("/health")
        responses.append(response.json())

    # All responses should have same keys
    keys_set = [set(r.keys()) for r in responses]
    assert all(
        k == keys_set[0] for k in keys_set
    ), "Health endpoint schema inconsistent across calls"

    # Write evidence
    evidence_content = f"""**3 consecutive calls to /health**:
- Call 1 keys: {sorted(keys_set[0])}
- Call 2 keys: {sorted(keys_set[1])}
- Call 3 keys: {sorted(keys_set[2])}

**Consistency Validation**: ✅ PASS
- ✅ All calls return identical schema structure

---
**Phase VII ACT 3 Complete**: All probe contracts validated ✅
"""
    evidence_writer.append_section("Schema Consistency Validation", evidence_content)
