"""
Elasticsearch async client — singleton with connection pooling.
"""
from __future__ import annotations

import structlog
from elasticsearch import AsyncElasticsearch

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

_es_client: AsyncElasticsearch | None = None


async def get_es_client() -> AsyncElasticsearch:
    """Return singleton Elasticsearch async client."""
    global _es_client
    if _es_client is None:
        kwargs: dict = {
            "request_timeout": 30,
            "retry_on_timeout": True,
            "max_retries": 3,
        }
        if settings.ELASTICSEARCH_API_KEY:
            kwargs["api_key"] = settings.ELASTICSEARCH_API_KEY
        _es_client = AsyncElasticsearch(
            settings.ELASTICSEARCH_URL,
            **kwargs,
        )
        logger.info("elasticsearch_client_created", url=settings.ELASTICSEARCH_URL)
    return _es_client
