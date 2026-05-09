"""
Rate limiting middleware using Redis sliding window algorithm.

Limits:
- Per phone number: configurable (default 30/min)
- Global: configurable (default 1000/min)
"""
from __future__ import annotations

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.redis_client import get_redis_client

logger = structlog.get_logger(__name__)
settings = get_settings()

EXEMPT_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter backed by Redis."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        redis = await get_redis_client()
        now = int(time.time())
        window = 60  # 1-minute window

        # ── Global rate limit ──────────────────────────────────────────────
        global_key = f"ratelimit:global:{now // window}"
        global_count = await redis.incr(global_key)
        if global_count == 1:
            await redis.expire(global_key, window * 2)

        if global_count > settings.GLOBAL_RATE_LIMIT_PER_MINUTE:
            logger.warning("global_rate_limit_exceeded", count=global_count)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": window - (now % window),
                },
                headers={"Retry-After": str(window - (now % window))},
            )

        # ── Per-client rate limit (webhook uses phone number, others use IP) ─
        client_id = self._get_client_id(request)
        client_key = f"ratelimit:client:{client_id}:{now // window}"
        client_count = await redis.incr(client_key)
        if client_count == 1:
            await redis.expire(client_key, window * 2)

        if client_count > settings.RATE_LIMIT_PER_MINUTE:
            logger.warning(
                "client_rate_limit_exceeded",
                client_id=client_id[:8],  # Log only prefix for privacy
                count=client_count,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests from this number. Please wait before sending another message.",
                    "retry_after": window - (now % window),
                },
                headers={"Retry-After": str(window - (now % window))},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, settings.RATE_LIMIT_PER_MINUTE - client_count)
        )
        return response

    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier for rate limiting."""
        # Use X-Forwarded-For when behind a reverse proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (leftmost = original client)
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return ip
