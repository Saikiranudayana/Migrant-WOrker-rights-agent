# Developer Guide

## Project Structure

```
shrammitra-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory
│   │   ├── core/                # Config, DB, ES, Redis, security, logging
│   │   ├── models/              # SQLAlchemy ORM + Pydantic schemas
│   │   ├── middleware/          # Security, rate limiter, logging, auth
│   │   ├── services/            # WhatsApp, voice, language, session
│   │   ├── rag/                 # Retriever, embeddings, index manager
│   │   ├── agents/              # Orchestrator, Bedrock client, safety
│   │   ├── api/                 # Route handlers (health, webhook, chat, admin)
│   │   └── utils/              # Conversation logger
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── security/
│   │   └── rag/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pytest.ini
├── frontend/
│   ├── app/                     # Next.js App Router pages
│   ├── services/                # API client (axios + React Query)
│   ├── package.json
│   └── Dockerfile
├── ingestion/
│   ├── pdf_parser/              # pdfplumber + PyPDF
│   ├── chunking/                # Sliding window text splitter
│   ├── embeddings/              # Jina v5 embedding pipeline
│   ├── sync_jobs/               # Orchestrator + source config
│   └── crawler/                 # Elastic Open Crawler config
├── infrastructure/
│   ├── terraform/               # AWS VPC, RDS, ElastiCache, S3, IAM
│   ├── nginx/                   # Reverse proxy + TLS
│   └── docker/postgres/         # DB init SQL
├── docs/
│   ├── architecture.md
│   ├── deployment.md
│   ├── security.md
│   ├── developer-guide.md       # ← this file
│   └── troubleshooting.md
├── .github/workflows/           # CI and deploy pipelines
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Common Development Tasks

### Run the backend locally

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Run tests

```bash
make test          # all tests
make test-unit     # unit tests only (fast, no external services)
make test-security # security tests
```

### Add a new API route

1. Create handler in `backend/app/api/your_route.py`.
2. Import and register in `backend/app/main.py` under `create_app()`.
3. Add integration test in `backend/tests/integration/test_your_route.py`.

### Add a new language

1. Add Unicode range in `backend/app/services/language_service.py` → `detect_language_by_script()`.
2. Add language code to `TRANSCRIBE_LANGUAGE_MAP` and `POLLY_VOICE_MAP` in `voice_service.py`.
3. Add disclaimer translation to `DISCLAIMER` dict in `safety_guardrail.py`.
4. Add `NO_CONTEXT_RESPONSE` translation in `safety_guardrail.py`.
5. Add field `content_{lang_code}` to ES index mapping in `rag/index_manager.py`.
6. Update `INDEX_MAPPING` — include the new field in the hybrid search query in `retriever.py`.

### Run the ingestion pipeline

```bash
# All sources
make ingest

# PDF sources only
python -m ingestion.sync_jobs.run_sync --source-type pdf

# Test with first 3 sources
python -m ingestion.sync_jobs.run_sync --limit 3
```

### Reindex Elasticsearch (zero-downtime)

```bash
make reindex
```

Creates `shrammitra_labour_docs_v{n+1}`, bulk re-indexes, swaps alias atomically.

---

## Key Design Patterns

### Singleton services

All stateful services (ES client, Redis, BedrockClient, etc.) use a `get_*()` function with module-level caching:

```python
_instance: Optional[MyService] = None

def get_my_service() -> MyService:
    global _instance
    if _instance is None:
        _instance = MyService(...)
    return _instance
```

### Background task for WhatsApp

Meta requires a 200 response within 5 seconds. The webhook handler:
1. Verifies HMAC signature (synchronous, fast).
2. Returns 200.
3. Queues `BackgroundTasks.add_task(_process_webhook_payload, ...)`.

The actual AI processing happens asynchronously.

### Prompt injection blocking

Safety guardrail runs **before** RAG retrieval. Blocked messages never reach Bedrock, saving tokens and preventing abuse.

### Index versioning

Elasticsearch index: `shrammitra_labour_docs_v1` (versioned)
Alias: `shrammitra_labour_docs` (what the app queries)

When reindexing: create `_v2` → bulk copy → atomic alias swap → delete `_v1`.
