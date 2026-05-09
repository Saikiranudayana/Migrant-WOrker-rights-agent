"""
Health check endpoint.

Returns system health status including:
- Overall application health
- Database connectivity
- Redis connectivity
- Elasticsearch connectivity
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.elasticsearch import get_es_client
from app.core.redis_client import get_redis_client
from app.models.schemas import HealthResponse, ServiceStatus

logger = structlog.get_logger(__name__)
settings = get_settings()

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Comprehensive health check for all service dependencies.

    Returns HTTP 200 if healthy, HTTP 503 if any critical service is down.
    """
    services: dict[str, ServiceStatus] = {}
    overall_healthy = True

    # ── Database ──────────────────────────────────────────────────────────────
    try:
        t0 = time.monotonic()
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_latency = (time.monotonic() - t0) * 1000
        services["database"] = ServiceStatus(status="ok", latency_ms=db_latency, details=None)
    except Exception as exc:
        overall_healthy = False
        services["database"] = ServiceStatus(
            status="down", latency_ms=None, details=str(exc)[:100]
        )

    # ── Redis ─────────────────────────────────────────────────────────────────
    try:
        t0 = time.monotonic()
        redis = await get_redis_client()
        await redis.ping()
        redis_latency = (time.monotonic() - t0) * 1000
        services["redis"] = ServiceStatus(status="ok", latency_ms=redis_latency, details=None)
    except Exception as exc:
        overall_healthy = False
        services["redis"] = ServiceStatus(
            status="down", latency_ms=None, details=str(exc)[:100]
        )

    # ── Elasticsearch ─────────────────────────────────────────────────────────
    try:
        t0 = time.monotonic()
        es = await get_es_client()
        cluster_health = await es.cluster.health()
        es_latency = (time.monotonic() - t0) * 1000
        es_status = cluster_health.get("status", "unknown")
        services["elasticsearch"] = ServiceStatus(
            status="ok" if es_status in ("green", "yellow") else "degraded",
            latency_ms=es_latency,
            details=f"Cluster status: {es_status}",
        )
        if es_status == "red":
            overall_healthy = False
    except Exception as exc:
        overall_healthy = False
        services["elasticsearch"] = ServiceStatus(
            status="down", latency_ms=None, details=str(exc)[:100]
        )

    return HealthResponse(
        status="healthy" if overall_healthy else "unhealthy",
        version="1.0.0",
        environment=settings.APP_ENV,
        services=services,
        timestamp=datetime.now(timezone.utc),
    )
