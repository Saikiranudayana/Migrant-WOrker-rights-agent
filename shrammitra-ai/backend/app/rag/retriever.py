"""
RAG Retrieval Engine.

Implements hybrid search combining:
1. Dense vector search (Jina v5 multilingual embeddings) — semantic matching
2. BM25 full-text search — keyword matching with language-specific analyzers
3. Reciprocal Rank Fusion (RRF) — combines both rankings

This hybrid approach ensures:
- Multilingual queries match correctly (Hindi question → Kannada source)
- Exact legal terms (section numbers, act names) still match via BM25
- Relevance confidence gating to prevent hallucination

Every retrieved chunk MUST include a source URL and title for citation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import structlog

from app.core.config import get_settings
from app.core.elasticsearch import get_es_client
from app.rag.embeddings import get_embedding_service

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass
class RetrievedChunk:
    """A retrieved document chunk with metadata."""
    content: str
    title: str
    source_url: str
    source_type: str
    language: str
    score: float
    act_name: Optional[str] = None
    section: Optional[str] = None
    chunk_index: int = 0


class RAGRetriever:
    """
    Hybrid RAG retriever using Elasticsearch dense_vector + BM25.
    """

    async def retrieve(
        self,
        query: str,
        language: str = "en",
        top_k: int | None = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve the most relevant document chunks for a query.

        Uses hybrid search:
        1. Dense vector search on the `embedding` field
        2. BM25 full-text search on `content` fields
        3. RRF combination

        Args:
            query: The user's query (in any language)
            language: Detected language of the query
            top_k: Number of results to return

        Returns:
            List of RetrievedChunk ordered by relevance (best first)
        """
        k = top_k or settings.RAG_TOP_K
        es = await get_es_client()
        embedding_service = get_embedding_service()

        # Generate query embedding
        query_vector = await embedding_service.embed_query(query)

        # ── Hybrid Search Query ──────────────────────────────────────────────
        search_query = {
            "size": k,
            "query": {
                "bool": {
                    "should": [
                        # BM25 full-text on main content
                        {
                            "match": {
                                "content": {
                                    "query": query,
                                    "boost": 1.0,
                                }
                            }
                        },
                        # BM25 on title (higher boost — title matches are very relevant)
                        {
                            "match": {
                                "title": {
                                    "query": query,
                                    "boost": 2.0,
                                }
                            }
                        },
                        # Language-specific content field if available
                        {
                            "match": {
                                f"content_{language}": {
                                    "query": query,
                                    "boost": 1.5,
                                }
                            }
                        },
                    ],
                    "minimum_should_match": 0,
                }
            },
            # Dense vector KNN search
            "knn": {
                "field": "embedding",
                "query_vector": query_vector,
                "k": k * 2,
                "num_candidates": k * 10,
                "boost": 2.0,
            },
            "_source": {
                "excludes": ["embedding", "content_hi", "content_kn",
                             "content_ta", "content_te", "content_bn"]
            },
            "highlight": {
                "fields": {"content": {"number_of_fragments": 2, "fragment_size": 200}},
                "pre_tags": [""],
                "post_tags": [""],
            },
        }

        try:
            response = await es.search(
                index=settings.ELASTICSEARCH_INDEX_ALIAS,
                body=search_query,
            )
        except Exception as exc:
            logger.error("elasticsearch_search_failed", error=str(exc))
            return []

        hits = response["hits"]["hits"]
        chunks: List[RetrievedChunk] = []

        for hit in hits:
            source = hit["_source"]
            score = hit["_score"] or 0.0

            # Normalize score to 0–1 range (ES scores are unbounded)
            normalized_score = min(score / 10.0, 1.0)

            # Skip results below confidence threshold
            if normalized_score < settings.RAG_SIMILARITY_THRESHOLD:
                logger.debug(
                    "chunk_below_threshold",
                    score=normalized_score,
                    threshold=settings.RAG_SIMILARITY_THRESHOLD,
                )
                continue

            # Use highlighted excerpt if available
            highlights = hit.get("highlight", {}).get("content", [])
            excerpt = " ... ".join(highlights) if highlights else source.get("content", "")[:500]

            chunks.append(
                RetrievedChunk(
                    content=excerpt,
                    title=source.get("title", ""),
                    source_url=source.get("source_url", ""),
                    source_type=source.get("source_type", "website"),
                    language=source.get("language", "en"),
                    score=normalized_score,
                    act_name=source.get("act_name"),
                    section=source.get("section"),
                    chunk_index=source.get("chunk_index", 0),
                )
            )

        logger.info(
            "retrieval_complete",
            query_length=len(query),
            language=language,
            results=len(chunks),
            top_score=chunks[0].score if chunks else 0.0,
        )
        return chunks

    def format_context(self, chunks: List[RetrievedChunk]) -> str:
        """
        Format retrieved chunks into a context string for the LLM.

        Each chunk is prefixed with its source for citation tracking.
        """
        if not chunks:
            return ""

        parts = []
        for i, chunk in enumerate(chunks, 1):
            source_line = f"[Source {i}]: {chunk.title} ({chunk.source_url})"
            if chunk.act_name:
                source_line += f" — {chunk.act_name}"
                if chunk.section:
                    source_line += f", {chunk.section}"
            parts.append(f"{source_line}\n{chunk.content}")

        return "\n\n---\n\n".join(parts)

    def extract_citations(self, chunks: List[RetrievedChunk]) -> List[dict]:
        """Extract citation metadata from retrieved chunks for the response."""
        seen = set()
        citations = []
        for chunk in chunks:
            if chunk.source_url not in seen:
                seen.add(chunk.source_url)
                citations.append({
                    "title": chunk.title,
                    "url": chunk.source_url,
                    "excerpt": chunk.content[:200],
                    "confidence": round(chunk.score, 3),
                })
        return citations


_retriever: RAGRetriever | None = None


def get_rag_retriever() -> RAGRetriever:
    """Return singleton RAGRetriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever
