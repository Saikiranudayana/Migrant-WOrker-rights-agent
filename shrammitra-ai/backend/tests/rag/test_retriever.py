"""Tests for the RAG retriever."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.retriever import RAGRetriever, RetrievedChunk


@pytest.fixture
def mock_es():
    es = AsyncMock()
    es.search = AsyncMock(return_value={
        "hits": {
            "hits": [
                {
                    "_id": "doc1",
                    "_score": 8.5,
                    "_source": {
                        "content": "The minimum wage in Karnataka for unskilled workers is ₹15,000.",
                        "title": "Karnataka Minimum Wages Notification",
                        "source_url": "https://labour.karnataka.gov.in/mw.pdf",
                        "source_type": "pdf",
                        "act_name": "Minimum Wages Act, 1948",
                        "section": "Section 4",
                        "chunk_index": 0,
                    },
                },
                {
                    "_id": "doc2",
                    "_score": 7.2,
                    "_source": {
                        "content": "Workers may approach the Labour Commissioner for wage disputes.",
                        "title": "Karnataka Labour Department Portal",
                        "source_url": "https://labour.karnataka.gov.in/",
                        "source_type": "website",
                        "act_name": None,
                        "section": None,
                        "chunk_index": 1,
                    },
                },
            ]
        }
    })
    return es


@pytest.fixture
def mock_embedding_service():
    svc = AsyncMock()
    svc.embed_query = AsyncMock(return_value=[0.1] * 1024)
    return svc


@pytest.fixture
def retriever(mock_es, mock_embedding_service):
    return RAGRetriever(
        es_client=mock_es,
        embedding_service=mock_embedding_service,
        index_name="shrammitra_labour_docs",
        similarity_threshold=0.3,
        k=5,
    )


class TestRAGRetriever:
    async def test_retrieve_returns_chunks(self, retriever):
        chunks = await retriever.retrieve("minimum wage Karnataka", language="en")
        assert len(chunks) == 2
        assert isinstance(chunks[0], RetrievedChunk)
        assert chunks[0].score >= chunks[1].score  # sorted by score

    async def test_retrieve_populates_fields(self, retriever):
        chunks = await retriever.retrieve("minimum wage Karnataka", language="en")
        chunk = chunks[0]
        assert chunk.content
        assert chunk.source_url
        assert chunk.source_title

    async def test_format_context_produces_string(self, retriever):
        chunks = await retriever.retrieve("minimum wage", language="en")
        context = retriever.format_context(chunks)
        assert isinstance(context, str)
        assert len(context) > 0

    async def test_extract_citations_deduped(self, retriever):
        chunks = await retriever.retrieve("minimum wage", language="en")
        # Add duplicate URL
        chunks.append(chunks[0])
        citations = retriever.extract_citations(chunks)
        urls = [c["url"] for c in citations]
        assert len(urls) == len(set(urls))  # no duplicates
