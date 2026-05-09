"""
Elasticsearch document indexer for the ingestion pipeline.

Handles:
- Batch upsert of document chunks
- Content deduplication via doc_hash
- Progress tracking
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import List

import structlog
from elasticsearch import AsyncElasticsearch, helpers

from ingestion.chunking.chunker import DocumentChunk
from ingestion.embeddings.embed_documents import EmbeddingPipeline

logger = structlog.get_logger(__name__)


class DocumentIndexer:
    """Batch-indexes document chunks into Elasticsearch."""

    def __init__(
        self,
        es_client: AsyncElasticsearch,
        index_name: str,
        embedding_pipeline: EmbeddingPipeline,
        batch_size: int = 50,
    ) -> None:
        self._es = es_client
        self._index = index_name
        self._embedding = embedding_pipeline
        self._batch_size = batch_size

    async def index_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Index a list of document chunks with embeddings.

        Returns number of successfully indexed documents.
        """
        if not chunks:
            return 0

        indexed_count = 0

        # Process in batches
        for i in range(0, len(chunks), self._batch_size):
            batch = chunks[i: i + self._batch_size]
            texts = [c.content for c in batch]

            # Generate embeddings for the batch
            embeddings = await self._embedding.embed_batch(texts)

            # Prepare ES bulk actions
            actions = []
            for chunk, embedding in zip(batch, embeddings):
                doc_id = hashlib.sha256(
                    f"{chunk.source_url}:{chunk.chunk_index}".encode()
                ).hexdigest()[:32]

                doc = {
                    "_index": self._index,
                    "_id": doc_id,
                    "_source": {
                        "title": chunk.title,
                        "content": chunk.content,
                        "embedding": embedding,
                        "source_url": chunk.source_url,
                        "source_title": chunk.title,
                        "source_type": chunk.source_type,
                        "language": chunk.language,
                        "chunk_index": chunk.chunk_index,
                        "total_chunks": chunk.total_chunks,
                        "act_name": chunk.act_name,
                        "section": chunk.section,
                        "doc_hash": chunk.doc_hash,
                        "indexed_at": datetime.now(timezone.utc).isoformat(),
                    },
                }
                actions.append(doc)

            # Bulk upsert
            success, errors = await helpers.async_bulk(
                self._es,
                actions,
                raise_on_error=False,
                max_retries=3,
            )
            indexed_count += success

            if errors:
                logger.error(
                    "bulk_index_errors",
                    error_count=len(errors),
                    first_error=str(errors[0])[:200],
                )

            logger.info(
                "batch_indexed",
                batch_num=i // self._batch_size + 1,
                success=success,
                errors=len(errors),
            )

        return indexed_count
