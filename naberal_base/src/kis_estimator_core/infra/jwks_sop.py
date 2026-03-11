"""
JWKS SOP - Supabase Auth JWKS Health Management (SB-02 Compliance)
===================================================================

Purpose: Implement JWKS Standard Operating Procedure (500→503→200 recovery)
Compliance: SB-02 (JWKS health SOP with evidence capture)

JWKS Health States:
- 500 Internal Server Error → Wait 30s, retry
- 503 Service Unavailable → Wait 60s, exponential backoff
- 200 OK → Cache for 1 hour, normal operation

Recovery Procedure:
1. Detect failure (500/503)
2. Log error with timestamp + traceId
3. Exponential backoff (30s, 60s, 120s, 300s)
4. Return cached JWKS if available (stale-while-revalidate)
5. If cache expired + JWKS unavailable → Reject auth with 503
6. Capture evidence to EvidencePack_v2/ci/jwks_failures/

Usage:
    from kis_estimator_core.infra.jwks_sop import fetch_jwks_with_sop

    jwks = await fetch_jwks_with_sop(
        jwks_url="https://project.supabase.co/auth/v1/.well-known/jwks.json"
    )
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

import httpx

# Import from SSOT (LAW-02: Single Source of Truth)
from kis_estimator_core.core.ssot.constants import (
    DEFAULT_BACKOFF_SECONDS,
    DEFAULT_CACHE_TTL,
    DEFAULT_MAX_RETRIES,
    EVIDENCE_DIR,
)

logger = logging.getLogger(__name__)


# ==========================================================================
# CONSTANTS (SSOT imports above)
# ==========================================================================


# ==========================================================================
# DATA STRUCTURES
# ==========================================================================
@dataclass
class JWKSFailureEvidence:
    """Evidence captured when JWKS fetch fails (SB-02 compliance)."""

    timestamp: str
    jwks_url: str
    status_code: int
    response_headers: dict[str, str]
    response_body: str
    attempt: int
    total_attempts: int
    backoff_seconds: int
    cache_available: bool
    trace_id: str | None = None
    error_message: str | None = None


@dataclass
class JWKSFetchResult:
    """Result of JWKS fetch operation."""

    success: bool
    jwks: dict | None
    status_code: int | None
    from_cache: bool
    attempts: int
    evidence_path: str | None = None
    error: str | None = None


# ==========================================================================
# JWKS CACHE (Simple In-Memory Cache)
# ==========================================================================
class JWKSCache:
    """Simple in-memory cache for JWKS responses."""

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._expiry: dict[str, datetime] = {}

    def get(self, key: str) -> dict | None:
        """Get cached JWKS if not expired."""
        if key not in self._cache:
            return None

        if key in self._expiry and datetime.utcnow() > self._expiry[key]:
            # Expired
            del self._cache[key]
            del self._expiry[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: dict, ttl: int = DEFAULT_CACHE_TTL):
        """Cache JWKS with TTL."""
        self._cache[key] = value
        self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)

    def has(self, key: str) -> bool:
        """Check if key exists in cache (even if expired)."""
        return key in self._cache

    def clear(self):
        """Clear all cached JWKS."""
        self._cache.clear()
        self._expiry.clear()


# Global JWKS cache instance
_jwks_cache = JWKSCache()


# ==========================================================================
# EVIDENCE CAPTURE
# ==========================================================================
def save_jwks_failure_evidence(evidence: JWKSFailureEvidence) -> str:
    """
    Save JWKS failure evidence to EvidencePack_v2/ci/jwks_failures/.

    Args:
        evidence: Failure evidence to save

    Returns:
        Path to saved evidence file
    """
    # Ensure evidence directory exists
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate filename: jwks_failure_{timestamp}_{status_code}.json
    filename = f"jwks_failure_{evidence.timestamp.replace(':', '-')}_{evidence.status_code}.json"
    filepath = EVIDENCE_DIR / filename

    # Save evidence as JSON
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(asdict(evidence), f, indent=2, ensure_ascii=False)

    logger.info(f"JWKS failure evidence saved: {filepath}")

    return str(filepath)


# ==========================================================================
# JWKS FETCH WITH SOP
# ==========================================================================
async def fetch_jwks_with_sop(
    jwks_url: str,
    cache_ttl: int = DEFAULT_CACHE_TTL,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: list[int] | None = None,
    timeout: int = 10,
    trace_id: str | None = None,
) -> JWKSFetchResult:
    """
    Fetch JWKS with SOP-compliant retry logic and evidence capture.

    SB-02: JWKS SOP (500→503→200 recovery with evidence)

    Args:
        jwks_url: JWKS endpoint URL (e.g., https://project.supabase.co/auth/v1/.well-known/jwks.json)
        cache_ttl: Cache TTL in seconds (default: 3600 = 1 hour)
        max_retries: Maximum retry attempts (default: 4)
        backoff_seconds: Backoff strategy in seconds (default: [30, 60, 120, 300])
        timeout: HTTP request timeout in seconds (default: 10)
        trace_id: Optional trace ID for request tracking

    Returns:
        JWKSFetchResult with JWKS or error information

    Raises:
        ValueError: If JWKS validation fails (missing 'keys' field)

    Example:
        >>> result = await fetch_jwks_with_sop("https://project.supabase.co/auth/v1/.well-known/jwks.json")
        >>> if result.success:
        ...     print(f"JWKS fetched (from_cache={result.from_cache})")
        ...     print(f"Keys: {len(result.jwks['keys'])}")
        ... else:
        ...     print(f"JWKS fetch failed: {result.error}")
    """
    if backoff_seconds is None:
        backoff_seconds = DEFAULT_BACKOFF_SECONDS

    # Check cache first
    cache_key = f"jwks:{jwks_url}"
    cached_jwks = _jwks_cache.get(cache_key)

    if cached_jwks:
        logger.info(f"JWKS cache hit for {jwks_url}")
        return JWKSFetchResult(
            success=True, jwks=cached_jwks, status_code=200, from_cache=True, attempts=0
        )

    # Fetch from endpoint with retry logic
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    f"Fetching JWKS from {jwks_url} (attempt {attempt}/{max_retries})..."
                )

                response = await client.get(jwks_url)

                # SUCCESS: 200 OK
                if response.status_code == 200:
                    jwks = response.json()

                    # Validate JWKS structure
                    if "keys" not in jwks:
                        raise ValueError(
                            f"Invalid JWKS response: missing 'keys' field. "
                            f"Response: {json.dumps(jwks)[:200]}"
                        )

                    # Cache the result
                    _jwks_cache.set(cache_key, jwks, ttl=cache_ttl)

                    logger.info(
                        f"JWKS fetched successfully: {len(jwks.get('keys', []))} keys "
                        f"(cached for {cache_ttl}s)"
                    )

                    return JWKSFetchResult(
                        success=True,
                        jwks=jwks,
                        status_code=200,
                        from_cache=False,
                        attempts=attempt,
                    )

                # FAILURE: 500 or 503
                elif response.status_code in (500, 503):
                    # Capture evidence
                    evidence = JWKSFailureEvidence(
                        timestamp=datetime.utcnow().isoformat(),
                        jwks_url=jwks_url,
                        status_code=response.status_code,
                        response_headers=dict(response.headers),
                        response_body=response.text[:1000],  # First 1000 chars
                        attempt=attempt,
                        total_attempts=max_retries,
                        backoff_seconds=backoff_seconds[
                            min(attempt - 1, len(backoff_seconds) - 1)
                        ],
                        cache_available=_jwks_cache.has(cache_key),
                        trace_id=trace_id,
                        error_message=f"JWKS endpoint returned {response.status_code}",
                    )
                    evidence_path = save_jwks_failure_evidence(evidence)

                    logger.warning(
                        f"JWKS fetch failed with {response.status_code} "
                        f"(attempt {attempt}/{max_retries}). "
                        f"Evidence saved: {evidence_path}"
                    )

                    # Check if we have stale cache we can use
                    if _jwks_cache.has(cache_key):
                        stale_jwks = _jwks_cache._cache.get(cache_key)
                        logger.warning(
                            f"JWKS endpoint unavailable ({response.status_code}), "
                            f"using stale cached version"
                        )
                        return JWKSFetchResult(
                            success=True,
                            jwks=stale_jwks,
                            status_code=response.status_code,
                            from_cache=True,
                            attempts=attempt,
                            evidence_path=evidence_path,
                        )

                    # Exponential backoff
                    if attempt < max_retries:
                        backoff = backoff_seconds[
                            min(attempt - 1, len(backoff_seconds) - 1)
                        ]
                        logger.info(
                            f"Backing off for {backoff} seconds before retry..."
                        )
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        # Max retries exhausted, no cache available
                        return JWKSFetchResult(
                            success=False,
                            jwks=None,
                            status_code=response.status_code,
                            from_cache=False,
                            attempts=attempt,
                            evidence_path=evidence_path,
                            error=f"JWKS endpoint unavailable ({response.status_code}), no cached version",
                        )

                # OTHER ERROR: Unexpected status code
                else:
                    logger.error(
                        f"Unexpected JWKS response status: {response.status_code} "
                        f"(body: {response.text[:200]})"
                    )

                    return JWKSFetchResult(
                        success=False,
                        jwks=None,
                        status_code=response.status_code,
                        from_cache=False,
                        attempts=attempt,
                        error=f"Unexpected status code: {response.status_code}",
                    )

            except httpx.TimeoutException as e:
                logger.error(
                    f"JWKS fetch timeout (attempt {attempt}/{max_retries}): {e}"
                )

                if attempt < max_retries:
                    backoff = backoff_seconds[
                        min(attempt - 1, len(backoff_seconds) - 1)
                    ]
                    await asyncio.sleep(backoff)
                    continue
                else:
                    return JWKSFetchResult(
                        success=False,
                        jwks=None,
                        status_code=None,
                        from_cache=False,
                        attempts=attempt,
                        error=f"Timeout after {max_retries} attempts",
                    )

            except Exception as e:
                logger.error(f"JWKS fetch error (attempt {attempt}/{max_retries}): {e}")

                if attempt < max_retries:
                    backoff = backoff_seconds[
                        min(attempt - 1, len(backoff_seconds) - 1)
                    ]
                    await asyncio.sleep(backoff)
                    continue
                else:
                    return JWKSFetchResult(
                        success=False,
                        jwks=None,
                        status_code=None,
                        from_cache=False,
                        attempts=attempt,
                        error=str(e),
                    )

    # Should never reach here
    return JWKSFetchResult(
        success=False,
        jwks=None,
        status_code=None,
        from_cache=False,
        attempts=max_retries,
        error="Unknown error",
    )


# ==========================================================================
# CACHE MANAGEMENT
# ==========================================================================
def clear_jwks_cache():
    """Clear all cached JWKS (useful for testing or manual refresh)."""
    _jwks_cache.clear()
    logger.info("JWKS cache cleared")


def get_jwks_cache_status() -> dict:
    """Get current JWKS cache status (for monitoring/debugging)."""
    return {
        "cached_jwks": len(_jwks_cache._cache),
        "cache_keys": list(_jwks_cache._cache.keys()),
        "expiry_times": {
            key: expiry.isoformat() for key, expiry in _jwks_cache._expiry.items()
        },
    }


# ==========================================================================
# CLI ENTRY POINT (for testing)
# ==========================================================================
async def main():
    """Command-line entry point for JWKS SOP testing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Supabase JWKS SOP Tester (SB-02 Compliance)"
    )
    parser.add_argument("--url", required=True, help="JWKS endpoint URL")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"Maximum retry attempts (default: {DEFAULT_MAX_RETRIES})",
    )
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear JWKS cache before fetching"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if args.clear_cache:
        clear_jwks_cache()

    logger.info("=" * 60)
    logger.info("JWKS SOP TEST")
    logger.info("=" * 60)
    logger.info(f"URL: {args.url}")
    logger.info(f"Max Retries: {args.max_retries}")
    logger.info("=" * 60)

    result = await fetch_jwks_with_sop(jwks_url=args.url, max_retries=args.max_retries)

    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(f"Success: {result.success}")
    print(f"Status Code: {result.status_code}")
    print(f"From Cache: {result.from_cache}")
    print(f"Attempts: {result.attempts}")

    if result.success:
        print(f"\nJWKS Keys: {len(result.jwks.get('keys', []))}")
        for key in result.jwks.get("keys", []):
            print(
                f"  - kid: {key.get('kid')}, kty: {key.get('kty')}, use: {key.get('use')}"
            )
    else:
        print(f"\nError: {result.error}")
        if result.evidence_path:
            print(f"Evidence: {result.evidence_path}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
