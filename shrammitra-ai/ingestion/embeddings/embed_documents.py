"""
Embedding pipeline wrapper for batch document embedding during ingestion.

Wraps Jina v5 (via Elastic Inference API or direct API) for the ingestion pipeline.
This is a standalone async wrapper that does not depend on the FastAPI app context.
"""
from __future__ import annotations

import os
from typing import List

import httpx
import structlog
from elasticsearch import AsyncElasticsearch

logger = structlog.get_logger(__name__)

JINA_MODEL_ID = "jina-embeddings-v3"
EMBEDDING_DIM = 1024


class EmbeddingPipeline:
    """
    Batch embedding generator for documents being ingested.

    Uses Elastic Inference API (recommended) with Jina API fallback.
    """

    def __init__(self, es_client: AsyncElasticsearch) -> None:
        self._es = es_client
        self._jina_api_key = os.environ.get("JINA_API_KEY", "")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts. Returns list of 1024-dim vectors."""
        if not texts:
            return []

        try:
            return await self._embed_via_elastic_inference(texts)
        except Exception as exc:
            logger.warning("elastic_inference_failed_fallback", error=str(exc)[:200])
            return await self._embed_via_jina_api(texts)

    async def _embed_via_elastic_inference(self, texts: List[str]) -> List[List[float]]:
        """Embed via Elastic Inference Endpoint (keeps data in Elastic cluster)."""
        response = await self._es.inference.inference(
            inference_id=JINA_MODEL_ID,
            body={"input": texts, "task_type": "text_embedding"},
        )
        return [item["embedding"] for item in response["text_embedding"]]

    async def _embed_via_jina_api(self, texts: List[str]) -> List[List[float]]:
        """Fallback: embed via Jina AI REST API."""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.jina.ai/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._jina_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": JINA_MODEL_ID,
                    "input": texts,
                    "dimensions": EMBEDDING_DIM,
                },
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
