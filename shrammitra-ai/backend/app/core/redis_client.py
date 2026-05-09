"""
Redis async client — singleton for session and cache management.
"""
from __future__ import annotations

import structlog
import redis.asyncio as aioredis

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

_redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """Return singleton Redis async client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        logger.info("redis_client_created", url=settings.REDIS_URL)
    return _redis_client
