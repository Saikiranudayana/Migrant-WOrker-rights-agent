"""
Request logging middleware — structured request/response logging.
"""
from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing and correlation IDs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        start_time = time.monotonic()

        # Bind request context for all logs in this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        logger.info(
            "request_started",
            user_agent=request.headers.get("User-Agent", "unknown")[:128],
        )

        response = await call_next(request)
        latency_ms = int((time.monotonic() - start_time) * 1000)

        logger.info(
            "request_completed",
            status_code=response.status_code,
            latency_ms=latency_ms,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{latency_ms}ms"
        return response
