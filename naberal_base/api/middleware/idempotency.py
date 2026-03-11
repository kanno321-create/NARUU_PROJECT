"""
Idempotency Middleware
Prevents duplicate request processing using Idempotency-Key header
"""

import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from api.cache import cache


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Idempotency middleware using Redis"""

    def __init__(self, app, ttl_seconds: int = 86400):
        super().__init__(app)
        self.ttl_seconds = ttl_seconds  # 24 hours default

    async def dispatch(self, request: Request, call_next):
        """Check idempotency key and return cached response if exists"""

        # Only apply to non-idempotent methods
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return await call_next(request)

        # Skip for health checks and docs
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Get idempotency key from header
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            # No idempotency key provided, process normally
            return await call_next(request)

        # Validate idempotency key format (basic check)
        if not self._is_valid_key(idempotency_key):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_idempotency_key",
                    "message": "Idempotency-Key must be a valid UUID or unique string (8-128 chars)",
                },
            )

        # Generate Redis key
        redis_key = f"idempotency:{idempotency_key}"

        # Check if request already processed
        cached_response = cache.get(redis_key)
        if cached_response:
            # Return cached response
            return JSONResponse(
                status_code=cached_response.get("status_code", 200),
                content=cached_response.get("body", {}),
                headers={
                    **cached_response.get("headers", {}),
                    "X-Idempotency-Cached": "true",
                },
            )

        # Process request
        response = await call_next(request)

        # Cache successful responses (2xx status codes)
        if 200 <= response.status_code < 300:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Parse JSON body
            try:
                body_json = json.loads(body.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                body_json = {"data": body.decode()}

            # Cache response
            cached_data = {
                "status_code": response.status_code,
                "body": body_json,
                "headers": dict(response.headers),
            }
            cache.set(redis_key, cached_data, ttl=self.ttl_seconds)

            # Return response with body
            return JSONResponse(
                status_code=response.status_code,
                content=body_json,
                headers={**dict(response.headers), "X-Idempotency-Cached": "false"},
            )

        # Don't cache error responses
        return response

    def _is_valid_key(self, key: str) -> bool:
        """Validate idempotency key format"""
        if not key or len(key) < 8 or len(key) > 128:
            return False

        # Allow alphanumeric, hyphens, underscores
        return all(c.isalnum() or c in "-_" for c in key)
