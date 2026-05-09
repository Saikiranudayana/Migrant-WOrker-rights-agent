"""
Full ingestion pipeline orchestrator.

Fetches → Parses → Chunks → Embeds → Indexes

Usage:
    python -m ingestion.sync_jobs.run_sync
    python -m ingestion.sync_jobs.run_sync --source-type pdf
    python -m ingestion.sync_jobs.run_sync --limit 5
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import List

import httpx
import structlog
from elasticsearch import AsyncElasticsearch

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../../../..")))

from ingestion.chunking.chunker import TextChunker
from ingestion.embeddings.embed_documents import EmbeddingPipeline
from ingestion.embeddings.indexer import DocumentIndexer
from ingestion.pdf_parser.parser import PDFParser
from ingestion.sync_jobs.sources_config import SOURCE_TYPE_PDF, SOURCE_TYPE_WEBSITE, SOURCES, SourceConfig

logger = structlog.get_logger(__name__)

# Minimal website scraper (BeautifulSoup) — PDF is primary source
try:
    from bs4 import BeautifulSoup  # type: ignore
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


async def fetch_pdf(url: str, timeout: int = 60) -> bytes:
    """Download a PDF from a URL and return raw bytes."""
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "ShramMitra-Indexer/1.0"})
        response.raise_for_status()
        return response.content


async def fetch_website_text(url: str, timeout: int = 30) -> str:
    """Fetch main text content from a website URL."""
    if not BS4_AVAILABLE:
        logger.warning("bs4_not_installed_skip_website", url=url)
        return ""
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "ShramMitra-Indexer/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Remove script/style
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)


async def process_source(
    source: SourceConfig,
    pdf_parser: PDFParser,
    chunker: TextChunker,
    indexer: DocumentIndexer,
) -> int:
    """Process a single source: fetch → parse → chunk → index. Returns chunk count."""
    log = logger.bind(url=source.url, source_type=source.source_type)
    log.info("processing_source")

    try:
        if source.source_type == SOURCE_TYPE_PDF:
            raw_bytes = await fetch_pdf(source.url)
            parsed = pdf_parser.parse_bytes(raw_bytes, source.url, title=source.title)
            content = parsed.content
            act_name = parsed.act_name or source.act_name
            doc_hash = parsed.doc_hash
        else:
            content = await fetch_website_text(source.url)
            act_name = source.act_name
            doc_hash = ""

        if not content or len(content) < 50:
            log.warning("empty_content_skip")
            return 0

        chunks = chunker.chunk_document(
            content=content,
            title=source.title,
            source_url=source.url,
            source_type=source.source_type,
            language=source.language,
            act_name=act_name,
            doc_hash=doc_hash,
        )

        if not chunks:
            log.warning("no_chunks_produced")
            return 0

        indexed = await indexer.index_chunks(chunks)
        log.info("source_indexed", chunks_produced=len(chunks), chunks_indexed=indexed)
        return indexed

    except httpx.HTTPError as exc:
        log.error("fetch_failed", error=str(exc))
        return 0
    except Exception as exc:
        log.exception("processing_failed", error=str(exc))
        return 0


async def run_sync(
    source_type_filter: str | None = None,
    limit: int | None = None,
) -> None:
    """Main ingestion orchestrator."""
    # Load config from env
    es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
    es_api_key = os.environ.get("ELASTICSEARCH_API_KEY", "")
    index_name = os.environ.get("ELASTICSEARCH_INDEX_ALIAS", "shrammitra_labour_docs")

    logger.info("ingestion_started", index=index_name, filter=source_type_filter)
    start = datetime.now(timezone.utc)

    # Build clients
    es = AsyncElasticsearch(
        es_url,
        api_key=es_api_key if es_api_key else None,
        request_timeout=30,
    )

    embedding_pipeline = EmbeddingPipeline(es)
    indexer = DocumentIndexer(
        es_client=es,
        index_name=index_name,
        embedding_pipeline=embedding_pipeline,
    )
    pdf_parser = PDFParser()
    chunker = TextChunker(chunk_size=800, chunk_overlap=150)

    # Filter and limit sources
    sources: List[SourceConfig] = sorted(SOURCES, key=lambda s: s.priority)
    if source_type_filter:
        sources = [s for s in sources if s.source_type == source_type_filter]
    if limit:
        sources = sources[:limit]

    logger.info("sources_to_process", count=len(sources))

    total_indexed = 0
    success_count = 0
    fail_count = 0

    for source in sources:
        indexed = await process_source(source, pdf_parser, chunker, indexer)
        if indexed > 0:
            success_count += 1
            total_indexed += indexed
        else:
            fail_count += 1

    await es.close()

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info(
        "ingestion_complete",
        total_sources=len(sources),
        success=success_count,
        failed=fail_count,
        total_chunks_indexed=total_indexed,
        elapsed_seconds=round(elapsed, 1),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="ShramMitra AI — Document Ingestion Pipeline")
    parser.add_argument(
        "--source-type",
        choices=["pdf", "website", "circular"],
        help="Filter by source type",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only the first N sources",
    )
    args = parser.parse_args()

    asyncio.run(run_sync(source_type_filter=args.source_type, limit=args.limit))


if __name__ == "__main__":
    main()
