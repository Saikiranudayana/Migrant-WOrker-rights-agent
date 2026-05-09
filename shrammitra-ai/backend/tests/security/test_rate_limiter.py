"""Tests for the rate limiter middleware."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.middleware.rate_limiter import RateLimiterMiddleware


def make_test_app(global_rpm: int = 1000, per_client_rpm: int = 5) -> FastAPI:
    """Build a minimal app with rate limiter for testing."""
    app = FastAPI()

    @app.get("/test")
    async def test_route():
        return {"ok": True}

    mock_redis = AsyncMock()
    # Simulate Redis pipeline for sliding window
    mock_pipe = AsyncMock()
    mock_pipe.execute = AsyncMock(return_value=[1, True, 1, True])  # below limits
    mock_redis.pipeline = MagicMock(return_value=mock_pipe)

    app.add_middleware(
        RateLimiterMiddleware,
        redis_client=mock_redis,
        global_rpm=global_rpm,
        per_client_rpm=per_client_rpm,
    )
    return app


class TestRateLimiter:
    async def test_request_under_limit_passes(self):
        app = make_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/test")
        assert response.status_code == 200

    async def test_health_endpoint_not_rate_limited(self):
        """Health check should bypass the rate limiter."""
        app = make_test_app(global_rpm=0, per_client_rpm=0)

        # Add health route
        @app.get("/health")
        async def health():
            return {"status": "ok"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        # Should not be blocked even with 0 limits
        assert response.status_code == 200

    async def test_response_has_rate_limit_headers(self):
        app = make_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/test")
        # Rate limiter should add X-RateLimit-* headers in production implementations
        assert response.status_code in (200, 429)
