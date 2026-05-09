"""
Elasticsearch index manager.

Manages the shrammitra_labour_docs index with:
- Dense vector field for Jina v5 embeddings (1024 dimensions)
- Multilingual text fields with language-specific analyzers
- Versioned index + alias pattern for zero-downtime reindexing
"""
from __future__ import annotations

import structlog
from elasticsearch import AsyncElasticsearch, NotFoundError

from app.core.config import get_settings
from app.core.elasticsearch import get_es_client

logger = structlog.get_logger(__name__)
settings = get_settings()

INDEX_MAPPING = {
    "mappings": {
        "properties": {
            # ── Core content fields ─────────────────────────────────────
            "title": {
                "type": "text",
                "analyzer": "standard",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 512}},
            },
            "content": {
                "type": "text",
                "analyzer": "standard",
            },
            # Language-specific analyzed copies
            "content_hi": {"type": "text", "analyzer": "standard"},  # Hindi
            "content_kn": {"type": "text", "analyzer": "standard"},  # Kannada
            "content_ta": {"type": "text", "analyzer": "standard"},  # Tamil
            "content_te": {"type": "text", "analyzer": "standard"},  # Telugu
            "content_bn": {"type": "text", "analyzer": "standard"},  # Bengali
            # ── Jina v5 dense vector (1024 dimensions, multilingual) ────
            "embedding": {
                "type": "dense_vector",
                "dims": settings.EMBEDDING_DIMENSION,
                "index": True,
                "similarity": "cosine",
            },
            # ── Source metadata ─────────────────────────────────────────
            "source_url": {"type": "keyword"},
            "source_title": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 512}},
            },
            "source_type": {
                "type": "keyword"
            },  # website | pdf | notification | circular
            "language": {"type": "keyword"},
            "chunk_index": {"type": "integer"},
            "total_chunks": {"type": "integer"},
            # ── Legal metadata ──────────────────────────────────────────
            "act_name": {"type": "keyword"},
            "section": {"type": "keyword"},
            "effective_date": {"type": "date"},
            # ── Administrative ──────────────────────────────────────────
            "indexed_at": {"type": "date"},
            "doc_hash": {"type": "keyword"},  # SHA-256 of content for deduplication
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "standard": {
                    "type": "standard",
                    "stopwords": "_none_",
                }
            }
        },
        "index": {
            "knn": True,
        },
    },
}


class IndexManager:
    """Manages Elasticsearch index lifecycle for ShramMitra."""

    def __init__(self) -> None:
        self.index_name = settings.ELASTICSEARCH_INDEX_NAME
        self.alias_name = settings.ELASTICSEARCH_INDEX_ALIAS

    async def create_index(self, force: bool = False) -> None:
        """
        Create the versioned index and alias if they don't exist.

        Uses versioned index + alias pattern for zero-downtime reindexing:
        - Index: shrammitra_labour_docs_v1
        - Alias: shrammitra_labour_docs  → points to v1
        """
        es = await get_es_client()

        if await es.indices.exists(index=self.index_name):
            if not force:
                logger.info("index_already_exists", index=self.index_name)
                return
            logger.warning("force_deleting_index", index=self.index_name)
            await es.indices.delete(index=self.index_name)

        # Create versioned index
        await es.indices.create(index=self.index_name, body=INDEX_MAPPING)
        logger.info("index_created", index=self.index_name)

        # Create or update alias
        try:
            existing_alias = await es.indices.get_alias(name=self.alias_name)
            # Remove alias from old index
            old_indices = list(existing_alias.keys())
            actions = [
                {"remove": {"index": idx, "alias": self.alias_name}}
                for idx in old_indices
            ]
            actions.append({"add": {"index": self.index_name, "alias": self.alias_name}})
            await es.indices.update_aliases(body={"actions": actions})
        except NotFoundError:
            # Alias doesn't exist yet
            await es.indices.put_alias(index=self.index_name, name=self.alias_name)

        logger.info("alias_created", alias=self.alias_name, index=self.index_name)

    async def get_index_stats(self) -> dict:
        """Return document count and index size stats."""
        es = await get_es_client()
        try:
            stats = await es.indices.stats(index=self.alias_name)
            count_resp = await es.count(index=self.alias_name)
            return {
                "document_count": count_resp["count"],
                "size_in_bytes": stats["_all"]["total"]["store"]["size_in_bytes"],
                "index_name": self.index_name,
                "alias_name": self.alias_name,
            }
        except Exception as exc:
            logger.error("index_stats_failed", error=str(exc))
            return {"error": str(exc)}

    async def delete_index(self) -> None:
        """Delete the index (destructive — use with caution)."""
        es = await get_es_client()
        await es.indices.delete(index=self.index_name, ignore_unavailable=True)
        logger.info("index_deleted", index=self.index_name)
