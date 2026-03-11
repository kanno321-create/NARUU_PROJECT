"""
K-PEW Subsystem Health Check Module

REAL health checks for K-PEW system components:
- Database connectivity (Supabase PostgreSQL)
- LLM API availability (Claude API)
- Quality gates configuration
- Critical dependencies

NO MOCKS - All checks use real connections and APIs

REBUILD Phase C (T2): Unified with infra/db.check_database_health()
"""

import hashlib
import os
from datetime import datetime
from typing import Any

import anthropic

# Import unified async DB health check
from kis_estimator_core.infra.db import check_database_health


async def check_kpew_health_async() -> dict[str, Any]:
    """
    Async health check for K-PEW subsystem.

    Returns:
        dict: Health status with component-level details
        {
            "status": "healthy|degraded|unhealthy",
            "timestamp": "2025-10-14T12:34:56Z",
            "components": {
                "database": {"status": "ok|error", "latency_ms": 45, "error": null},
                "llm_api": {"status": "ok|error", "provider": "claude", "error": null},
                "quality_gates": {"status": "ok|error", "config_hash": "abc123", "error": null}
            },
            "version": "v1.3"
        }
    """
    components = {}
    overall_status = "healthy"

    # 1. Database connectivity check (REAL Supabase - unified with infra/db)
    db_health = await _check_database_async()
    components["database"] = db_health
    if db_health["status"] == "error":
        overall_status = "degraded" if overall_status == "healthy" else "unhealthy"

    # 2. LLM API availability check (REAL Claude API)
    llm_health = _check_llm_api()
    components["llm_api"] = llm_health
    if llm_health["status"] == "error":
        overall_status = "degraded"

    # 3. Quality gates configuration check
    gates_health = _check_quality_gates()
    components["quality_gates"] = gates_health
    if gates_health["status"] == "error":
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": components,
        "version": "v1.3",
    }


async def _check_database_async() -> dict[str, Any]:
    """
    Check REAL Supabase PostgreSQL connectivity (Async).

    Uses unified infra/db.check_database_health() implementation.

    Returns:
        dict: {"status": "ok|error", "latency_ms": int, "error": str|null}
    """
    try:
        start_time = datetime.utcnow()

        # Use unified DB health check (infra/db.py)
        health = await check_database_health()

        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        if health["connected"] and health["status"] in ["healthy", "empty"]:
            return {
                "status": "ok",
                "latency_ms": latency_ms,
                "timezone_utc": health.get("timezone_utc", False),
                "error": None,
            }
        else:
            return {
                "status": "error",
                "latency_ms": latency_ms,
                "error": health.get("error", "Database connection failed"),
            }

    except Exception as e:
        return {
            "status": "error",
            "latency_ms": 0,
            "error": f"Database check failed: {str(e)}",
        }


def _check_llm_api() -> dict[str, Any]:
    """
    Check REAL Claude API availability.

    Returns:
        dict: {"status": "ok|error", "provider": "claude", "error": str|null}
    """
    try:
        # REAL Claude API check (NO MOCKS!)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "provider": "claude",
                "error": "ANTHROPIC_API_KEY not configured",
            }

        client = anthropic.Anthropic(api_key=api_key)

        # Minimal API call to verify connectivity
        # Using the cheapest model and minimal tokens for health check
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "health"}],
        )

        if not response or not response.content:
            return {
                "status": "error",
                "provider": "claude",
                "error": "API returned empty response",
            }

        return {"status": "ok", "provider": "claude", "error": None}

    except anthropic.APIError as e:
        return {
            "status": "error",
            "provider": "claude",
            "error": f"Claude API error: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "provider": "claude",
            "error": f"Unexpected error: {str(e)}",
        }


def _check_quality_gates() -> dict[str, Any]:
    """
    Check quality gates configuration file integrity.

    Returns:
        dict: {"status": "ok|error", "config_hash": str, "error": str|null}
    """
    try:
        # Check if quality gates YAML exists
        gates_path = "specs/gates/estimation.yaml"

        if not os.path.exists(gates_path):
            return {
                "status": "error",
                "config_hash": None,
                "error": f"Quality gates config not found: {gates_path}",
            }

        # Read and hash config file for integrity verification
        with open(gates_path, encoding="utf-8") as f:
            config_content = f.read()

        config_hash = hashlib.sha256(config_content.encode()).hexdigest()[:8]

        # Basic validation - check for required keys
        required_keys = ["rules", "balance_limit", "fit_score_min"]
        for key in required_keys:
            if key not in config_content:
                return {
                    "status": "error",
                    "config_hash": config_hash,
                    "error": f"Required key '{key}' not found in config",
                }

        return {"status": "ok", "config_hash": config_hash, "error": None}

    except Exception as e:
        return {
            "status": "error",
            "config_hash": None,
            "error": f"Config validation failed: {str(e)}",
        }
