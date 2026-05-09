"""
Embedding service using Jina v5 multilingual embeddings.

Jina Embeddings v3 is a frontier multilingual embedding model with:
- 1024 dimensions
- Support for 100+ languages including all Indian languages
- Superior multilingual semantic matching

In production, this calls Elastic's Inference Service (ELSER/Jina endpoint).
In development, falls back to a direct Jina API call.
"""
from __future__ import annotations

import asyncio
from typing import List

import httpx
import structlog

from app.core.config import get_settings
from app.core.elasticsearch import get_es_client

logger = structlog.get_logger(__name__)
settings = get_settings()

JINA_API_URL = "https://api.jina.ai/v1/embeddings"


class EmbeddingService:
    """
    Generate multilingual embeddings using Jina v3 via Elastic Inference API.

    The Elastic Inference Service hosts the Jina model and exposes it
    via the _inference API, keeping all data within the Elastic cluster.
    """

    def __init__(self) -> None:
        self._inference_id = "jina-embeddings-v3"

    async def embed_text(self, text: str) -> List[float]:
        """Generate a single embedding vector for a text string."""
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.

        Tries Elastic Inference API first; falls back to direct Jina API.
        """
        try:
            return await self._embed_via_elastic_inference(texts)
        except Exception as exc:
            logger.warning(
                "elastic_inference_failed_falling_back_to_jina_api",
                error=str(exc),
            )
            return await self._embed_via_jina_api(texts)

    async def _embed_via_elastic_inference(
        self, texts: List[str]
    ) -> List[List[float]]:
        """
        Use Elastic's _inference API to generate embeddings.

        This keeps embeddings within the Elastic ecosystem and supports
        the Jina v3 model as a hosted inference endpoint.
        """
        es = await get_es_client()
        results = []
        # Elastic inference API processes one at a time or in small batches
        for text in texts:
            response = await es.inference.inference(
                inference_id=self._inference_id,
                body={"input": text},
            )
            # Extract embedding from response
            embedding = response["text_embedding"][0]["embedding"]
            results.append(embedding)
        return results

    async def _embed_via_jina_api(self, texts: List[str]) -> List[List[float]]:
        """
        Direct Jina AI API call as fallback.

        Note: For production, use Elastic Inference Service to keep
        data within your security perimeter.
        """
        # Truncate texts to avoid API limits
        truncated = [t[:8192] for t in texts]

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                JINA_API_URL,
                json={
                    "model": "jina-embeddings-v3",
                    "input": truncated,
                    "task": "retrieval.query",
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.ELASTICSEARCH_API_KEY}",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]

    async def embed_query(self, query: str) -> List[float]:
        """
        Embed a search query (uses 'retrieval.query' task type for Jina v3).

        Query embeddings use a different task type than document embeddings
        in asymmetric retrieval settings.
        """
        return await self.embed_text(query)


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Return singleton EmbeddingService instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
