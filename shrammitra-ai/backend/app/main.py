"""
ShramMitra AI — FastAPI Application Entry Point.

Multilingual WhatsApp AI assistant for migrant worker rights in Bengaluru.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import admin, chat, health, webhook
from app.core.config import get_settings
from app.core.database import init_db
from app.core.elasticsearch import get_es_client
from app.core.redis_client import get_redis_client
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.security import SecurityHeadersMiddleware

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("starting_shrammitra_ai", environment=settings.APP_ENV)

    # Initialize database
    await init_db()
    logger.info("database_ready")

    # Verify Elasticsearch connection
    es = await get_es_client()
    info = await es.info()
    logger.info("elasticsearch_ready", version=info["version"]["number"])

    # Verify Redis connection
    redis = await get_redis_client()
    await redis.ping()
    logger.info("redis_ready")

    logger.info("shrammitra_ai_ready", port=settings.APP_PORT)
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("shutting_down_shrammitra_ai")
    es_client = await get_es_client()
    await es_client.close()
    redis_client = await get_redis_client()
    await redis_client.aclose()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ShramMitra AI",
        summary="Multilingual WhatsApp AI Assistant for Migrant Worker Rights",
        description=(
            "ShramMitra AI helps migrant workers in Bengaluru understand their labour "
            "rights in their native language via WhatsApp. "
            "**Disclaimer:** This assistant provides informational guidance only "
            "and is not legal counsel."
        ),
        version="1.0.0",
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
        openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
        lifespan=lifespan,
    )

    # ── Trusted hosts (production) ─────────────────────────────────────────
    if settings.APP_ENV == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    # ── Custom middleware ─────────────────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimiterMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # ── Prometheus metrics ────────────────────────────────────────────────────
    if settings.ENABLE_METRICS:
        Instrumentator(
            should_group_status_codes=False,
            excluded_handlers=["/health", "/metrics"],
        ).instrument(app).expose(app, endpoint="/metrics")

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health.router, tags=["Health"])
    app.include_router(webhook.router, prefix="/webhook", tags=["WhatsApp"])
    app.include_router(chat.router, prefix="/chat", tags=["Chat"])
    app.include_router(admin.router, prefix="/admin", tags=["Admin"])

    # ── Global exception handlers ─────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred. Please try again.",
                "request_id": request.headers.get("X-Request-ID", "unknown"),
            },
        )

    return app


app = create_app()
