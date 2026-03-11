"""
Catalog Router - Real Supabase catalog_items query with Redis caching
NO MOCKS - Real database operations only
"""

import logging
import statistics
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List

from api.db import get_db
from api.cache import cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/catalog", tags=["catalog"])

# SSOT: 허용된 kind 목록
VALID_KINDS = {"breaker", "enclosure", "accessory", "busbar", "cable", "misc"}


@router.get("/items")
async def list_catalog_items(
    kind: Optional[str] = Query(
        None, description="Filter by kind (breaker, enclosure, etc)"
    ),
    q: Optional[str] = Query(None, description="Search query for name or sku"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
):
    """
    List catalog items from shared.catalog_items table (with Redis cache)

    REAL DATABASE QUERY - NO MOCKS
    Cache: 1 hour TTL per query combination

    Returns:
        {
            "items": [...],
            "pagination": {
                "page": 1,
                "size": 20,
                "total": 276,
                "pages": 14
            }
        }
    """
    # Validate kind parameter
    if kind and kind not in VALID_KINDS:
        import uuid
        raise HTTPException(
            status_code=422,
            detail={
                "code": "CAT-VAL",
                "message": f"Invalid kind: {kind}",
                "hint": f"Valid kinds: {sorted(VALID_KINDS)}",
                "traceId": str(uuid.uuid4()),
                "meta": {"dedupKey": "catalog-kind-validation-error"},
            },
        )

    # Generate cache key from query parameters
    cache_key = f"catalog:items:{kind or 'all'}:{q or 'none'}:{page}:{size}"
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"✅ Cache HIT: {cache_key}")
        return cached

    try:
        # Build WHERE clause
        where_clauses = []
        params = {}

        if kind:
            where_clauses.append("kind = :kind")
            params["kind"] = kind

        if q:
            where_clauses.append("(name ILIKE :search OR sku ILIKE :search)")
            params["search"] = f"%{q}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Count total
        count_query = text(
            f"""
            SELECT COUNT(*) as total
            FROM shared.catalog_items
            WHERE {where_sql}
        """
        )
        count_result = await db.execute(count_query, params)
        total = count_result.scalar()

        # Calculate pagination
        offset = (page - 1) * size
        pages = (total + size - 1) // size

        # Query items
        # Note: DB schema uses 'price', API returns 'unit_price' (aliased)
        items_query = text(
            f"""
            SELECT
                id, kind, sku, name, spec,
                price AS unit_price,
                currency,
                is_active,
                meta,
                created_at, updated_at
            FROM shared.catalog_items
            WHERE {where_sql}
            ORDER BY kind, sku
            LIMIT :limit OFFSET :offset
        """
        )

        items_result = await db.execute(
            items_query, {**params, "limit": size, "offset": offset}
        )

        items = []
        for row in items_result:
            items.append(
                {
                    "id": str(row.id),
                    "kind": row.kind,
                    "sku": row.sku,
                    "name": row.name,
                    "spec": row.spec,
                    "unit_price": float(row.unit_price),
                    "currency": row.currency,
                    "is_active": row.is_active,
                    "meta": row.meta,
                    "created_at": (
                        row.created_at.isoformat() if row.created_at else None
                    ),
                    "updated_at": (
                        row.updated_at.isoformat() if row.updated_at else None
                    ),
                }
            )

        response = {
            "items": items,
            "pagination": {"page": page, "size": size, "total": total, "pages": pages},
        }

        # Cache for 15 minutes (Phase VII: 900s TTL for catalog reads)
        cache.set(cache_key, response, ttl=900)
        logger.info(f"💾 Cache MISS: {cache_key} (cached now, TTL=900s)")

        return response

    except Exception as e:
        logger.error(f"Catalog query error: {e}")
        # 5xx Fail Fast: 즉시 반환, 재시도 없음
        import uuid

        raise HTTPException(
            status_code=500,
            detail={
                "code": "DB_QUERY_ERROR",
                "message": "Database query failed",
                "hint": "Check database connection and query syntax",
                "traceId": str(uuid.uuid4()),
                "meta": {
                    "dedupKey": "catalog-query-error",
                    "exception": type(e).__name__,
                },
            },
        )


@router.get("/items/{sku}")
async def get_catalog_item(sku: str, db: AsyncSession = Depends(get_db)):
    """
    Get single catalog item by SKU (with Redis cache)

    REAL DATABASE QUERY - NO MOCKS
    Cache: 15 minutes TTL (Phase VII: 900s)
    """
    # Trim whitespace from SKU
    sku = sku.strip()

    # Try cache first
    cache_key = f"catalog:item:{sku}"
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"✅ Cache HIT: {cache_key}")
        return cached

    try:
        # Note: DB schema uses 'price', API returns 'unit_price' (aliased)
        query = text(
            """
            SELECT
                id, kind, sku, name, spec,
                price AS unit_price,
                currency,
                is_active,
                meta,
                created_at, updated_at
            FROM shared.catalog_items
            WHERE sku = :sku
            LIMIT 1
        """
        )

        result = await db.execute(query, {"sku": sku})
        row = result.first()

        if not row:
            import uuid
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "SKU_NOT_FOUND",
                    "message": f"SKU not found: {sku}",
                    "hint": "Check SKU spelling or use GET /v1/catalog/items to search",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "catalog-sku-not-found", "sku": sku},
                },
            )

        response = {
            "id": str(row.id),
            "kind": row.kind,
            "sku": row.sku,
            "name": row.name,
            "spec": row.spec,
            "unit_price": float(row.unit_price),
            "currency": row.currency,
            "is_active": row.is_active,
            "meta": row.meta,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }

        # Cache for 15 minutes (Phase VII: 900s TTL)
        cache.set(cache_key, response, ttl=900)
        logger.info(f"💾 Cache MISS: {cache_key} (cached now, TTL=900s)")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Catalog item query error: {e}")
        # 5xx Fail Fast: 즉시 반환, 재시도 없음
        import uuid

        raise HTTPException(
            status_code=500,
            detail={
                "code": "DB_QUERY_ERROR",
                "message": "Database query failed",
                "hint": "Check database connection and query syntax",
                "traceId": str(uuid.uuid4()),
                "meta": {
                    "dedupKey": "catalog-item-query-error",
                    "exception": type(e).__name__,
                },
            },
        )


@router.get("/stats")
async def get_catalog_stats(db: AsyncSession = Depends(get_db)):
    """
    Get catalog statistics by kind (with Redis cache)

    REAL DATABASE QUERY - NO MOCKS
    Cache: 1 hour TTL
    """
    # Try cache first
    cache_key = "catalog:stats"
    cached = cache.get(cache_key)
    if cached:
        logger.info("✅ Cache HIT: catalog stats")
        return cached

    try:
        query = text(
            """
            SELECT kind, COUNT(*) as count
            FROM shared.catalog_items
            GROUP BY kind
            ORDER BY kind
        """
        )

        result = await db.execute(query)

        stats = {}
        total = 0
        for row in result:
            stats[row.kind] = row.count
            total += row.count

        response = {"total": total, "by_kind": stats}

        # Cache for 15 minutes (Phase VII: 900s TTL for catalog reads)
        cache.set(cache_key, response, ttl=900)
        logger.info("💾 Cache MISS: catalog stats (cached now, TTL=900s)")

        return response

    except Exception as e:
        logger.error(f"Catalog stats error: {e}")
        # 5xx Fail Fast: 즉시 반환, 재시도 없음
        import uuid

        raise HTTPException(
            status_code=500,
            detail={
                "code": "DB_QUERY_ERROR",
                "message": "Database query failed",
                "hint": "Check database connection and query syntax",
                "traceId": str(uuid.uuid4()),
                "meta": {
                    "dedupKey": "catalog-stats-error",
                    "exception": type(e).__name__,
                },
            },
        )


@router.get("/metrics")
async def get_performance_metrics(
    endpoint: Optional[str] = Query(
        None, description="Filter by specific endpoint (e.g., 'v1:catalog:items')"
    )
):
    """
    Get performance metrics (p95, p99, avg response times) - Phase VII

    Uses Redis sorted sets populated by PerformanceMiddleware.
    Calculates percentiles from recent measurements (up to 1000 per endpoint).

    Query params:
        endpoint: Optional filter for specific endpoint (Redis key format)

    Returns:
        {
            "endpoints": {
                "v1:catalog:items": {
                    "count": 1000,
                    "avg_ms": 150.5,
                    "p50_ms": 145.2,
                    "p95_ms": 180.3,
                    "p99_ms": 210.5,
                    "min_ms": 50.1,
                    "max_ms": 250.8
                },
                ...
            }
        }
    """
    if not cache.enabled or not cache.client:
        import uuid
        raise HTTPException(
            status_code=503,
            detail={
                "code": "METRICS_UNAVAILABLE",
                "message": "Redis cache not enabled - metrics unavailable",
                "hint": "Configure REDIS_URL to enable performance metrics",
                "traceId": str(uuid.uuid4()),
                "meta": {"dedupKey": "metrics-cache-unavailable"},
            },
        )

    try:
        # Find all metrics keys
        pattern = (
            f"metrics:response_time:{endpoint}"
            if endpoint
            else "metrics:response_time:*"
        )
        metric_keys = cache.client.keys(pattern)

        if not metric_keys:
            return {"endpoints": {}, "message": "No metrics data available yet"}

        endpoints_data = {}

        for key in metric_keys:
            # Extract endpoint name from key
            # Key format: metrics:response_time:v1:catalog:items
            endpoint_name = key.replace("metrics:response_time:", "")

            # Get all measurements (sorted by score/timestamp)
            # ZRANGE returns list of values (response times in ms)
            measurements_raw = cache.client.zrange(key, 0, -1)

            if not measurements_raw:
                continue

            # Convert to floats
            measurements: List[float] = [float(m) for m in measurements_raw]
            count = len(measurements)

            if count == 0:
                continue

            # Calculate statistics
            avg_ms = statistics.mean(measurements)
            min_ms = min(measurements)
            max_ms = max(measurements)

            # Calculate percentiles
            if count == 1:
                p50_ms = p95_ms = p99_ms = measurements[0]
            elif count == 2:
                p50_ms = statistics.median(measurements)
                p95_ms = p99_ms = max_ms
            else:
                # Use statistics.quantiles for accurate percentile calculation
                # quantiles() requires n >= 2
                p50_ms = statistics.median(measurements)
                quantiles = statistics.quantiles(
                    measurements, n=100
                )  # 1-99 percentiles
                p95_ms = quantiles[94]  # 95th percentile (0-indexed)
                p99_ms = quantiles[98]  # 99th percentile

            endpoints_data[endpoint_name] = {
                "count": count,
                "avg_ms": round(avg_ms, 2),
                "p50_ms": round(p50_ms, 2),
                "p95_ms": round(p95_ms, 2),
                "p99_ms": round(p99_ms, 2),
                "min_ms": round(min_ms, 2),
                "max_ms": round(max_ms, 2),
            }

        return {"endpoints": endpoints_data}

    except Exception as e:
        logger.error(f"Metrics retrieval error: {e}")
        import uuid

        raise HTTPException(
            status_code=500,
            detail={
                "code": "METRICS_ERROR",
                "message": f"Failed to retrieve metrics: {str(e)}",
                "hint": "Check Redis connection and metrics data",
                "traceId": str(uuid.uuid4()),
                "meta": {"dedupKey": "metrics-error", "exception": type(e).__name__},
            },
        )


@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: Optional[str] = Body(
        None,
        description="Pattern to invalidate (e.g., 'catalog:items:*' or None for all)",
    )
):
    """
    Invalidate catalog cache - Phase VII

    Clears cached catalog data to force refresh from database.
    Useful after catalog updates or manual data changes.

    Body:
        pattern: Optional Redis key pattern (default: 'catalog:*' for all catalog caches)

    Returns:
        {
            "invalidated_keys": 15,
            "pattern": "catalog:*"
        }
    """
    if not cache.enabled or not cache.client:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "CACHE_UNAVAILABLE",
                "message": "Redis cache not enabled",
                "hint": "Configure REDIS_URL to enable cache management",
            },
        )

    try:
        # Default pattern: all catalog caches
        cache_pattern = pattern or "catalog:*"

        # Clear matching keys
        deleted_count = cache.clear_pattern(cache_pattern)

        logger.info(
            f"Cache invalidated: {deleted_count} keys matching '{cache_pattern}'"
        )

        return {
            "invalidated_keys": deleted_count,
            "pattern": cache_pattern,
            "message": f"Successfully invalidated {deleted_count} cache keys",
        }

    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        import uuid

        raise HTTPException(
            status_code=500,
            detail={
                "code": "CACHE_INVALIDATE_ERROR",
                "message": f"Failed to invalidate cache: {str(e)}",
                "hint": "Check Redis connection",
                "traceId": str(uuid.uuid4()),
                "meta": {
                    "dedupKey": "cache-invalidate-error",
                    "exception": type(e).__name__,
                },
            },
        )


@router.post("/cache/warm")
async def warm_cache(db: AsyncSession = Depends(get_db)):
    """
    Warm catalog cache - Phase VII

    Pre-loads frequently accessed catalog data into cache.
    Useful after cache invalidation or application startup.

    Warms:
    - Catalog stats
    - First page of items for each kind (breaker, enclosure, accessory)

    Returns:
        {
            "warmed_keys": 4,
            "details": [...]
        }
    """
    if not cache.enabled or not cache.client:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "CACHE_UNAVAILABLE",
                "message": "Redis cache not enabled",
                "hint": "Configure REDIS_URL to enable cache warming",
            },
        )

    try:
        warmed_keys = []

        # 1. Warm catalog stats
        stats_key = "catalog:stats"
        if not cache.get(stats_key):
            # Call the stats endpoint internally to populate cache
            _ = await get_catalog_stats(db)
            warmed_keys.append({"key": stats_key, "description": "catalog statistics"})

        # 2. Warm first page of items for major kinds
        major_kinds = ["breaker", "enclosure", "accessory"]
        for kind in major_kinds:
            cache_key = f"catalog:items:{kind}:none:1:20"
            if not cache.get(cache_key):
                # Call list endpoint internally to populate cache
                _ = await list_catalog_items(kind=kind, q=None, page=1, size=20, db=db)
                warmed_keys.append(
                    {"key": cache_key, "description": f"{kind} items (page 1)"}
                )

        logger.info(f"Cache warmed: {len(warmed_keys)} keys")

        return {
            "warmed_keys": len(warmed_keys),
            "details": warmed_keys,
            "message": f"Successfully warmed {len(warmed_keys)} cache keys",
        }

    except Exception as e:
        logger.error(f"Cache warming error: {e}")
        import uuid

        raise HTTPException(
            status_code=500,
            detail={
                "code": "CACHE_WARM_ERROR",
                "message": f"Failed to warm cache: {str(e)}",
                "hint": "Check database connection and cache configuration",
                "traceId": str(uuid.uuid4()),
                "meta": {"dedupKey": "cache-warm-error", "exception": type(e).__name__},
            },
        )
