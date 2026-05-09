# Architecture

## System Overview

ShramMitra AI is a multilingual WhatsApp AI assistant that answers labour law and rights questions for migrant workers in Bengaluru. It combines Retrieval-Augmented Generation (RAG) with Amazon Bedrock (Claude 3 Sonnet) to provide accurate, cited responses in Hindi, Kannada, Tamil, Telugu, Bengali, Odia, and English.

---

## Component Diagram

```
WhatsApp User
      │
      ▼ HTTPS POST (JSON)
Meta WhatsApp Business Cloud API
      │
      ▼
┌─────────────────────────────────────────────────┐
│  Nginx (TLS termination, rate limiting)         │
└─────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────┐
│  FastAPI Backend                                │
│                                                 │
│  Middleware stack:                              │
│    TrustedHost → CORS → SecurityHeaders         │
│    → RateLimiter (Redis) → RequestLogging       │
│                                                 │
│  POST /webhook/whatsapp                         │
│    1. HMAC-SHA256 signature verify              │
│    2. Return 200 immediately                    │
│    3. BackgroundTask: _handle_message()         │
│                                                 │
│  AgentCoreOrchestrator                          │
│    ├─ LanguageService (script + langdetect)     │
│    ├─ SafetyGuardrail (input check)             │
│    ├─ RAGRetriever                              │
│    │    ├─ EmbeddingService (Jina v5)           │
│    │    └─ Elasticsearch hybrid search          │
│    ├─ SafetyGuardrail (context check)           │
│    ├─ BedrockClient (Claude 3 Sonnet)           │
│    └─ SafetyGuardrail (output check)            │
│                                                 │
│  VoiceService (audio messages)                  │
│    ├─ AWS Transcribe (STT)                      │
│    └─ AWS Polly (TTS)                           │
│                                                 │
│  WhatsAppService → send reply                   │
│  ConversationLogger → PostgreSQL                │
│  SessionService → Redis                         │
└─────────────────────────────────────────────────┘
      │                  │                │
      ▼                  ▼                ▼
Elasticsearch        PostgreSQL         Redis
(documents + KNN)  (conversations)   (sessions, dedup,
                                      rate limiting)
```

---

## Data Flow for a Text Query

1. User sends WhatsApp message → Meta API delivers webhook POST.
2. Nginx forwards to FastAPI; HMAC signature verified.
3. `BackgroundTasks.add_task()` fires; 200 returned immediately to Meta.
4. Background task: phone number hashed, Redis dedup checked.
5. `AgentCoreOrchestrator.process_query()`:
   a. **Language detection** — Unicode script ranges (instant) → langdetect fallback.
   b. **Input guardrail** — sanitize, check 13 injection patterns.
   c. **RAG retrieval** — embed query via Jina v5 → Elasticsearch hybrid KNN+BM25 → top-5 chunks.
   d. **Context sufficiency check** — if score < threshold, return no-context response.
   e. **Bedrock generation** — Claude 3 Sonnet with system prompt, history (last 6 turns), context.
   f. **Output guardrail** — cap length, ensure disclaimer present.
6. Response sent via WhatsApp Business Cloud API.
7. Conversation + messages persisted to PostgreSQL.
8. Session (history, language, state) updated in Redis.

---

## Data Flow for a Voice Message

Same as above, plus:
- `VoiceService.speech_to_text()`: Download OGG → upload to S3 → AWS Transcribe → transcript text.
- After generation: `VoiceService.text_to_speech()` → Polly MP3 → S3 presigned URL.
- Both audio URL and text sent to user.

---

## Ingestion Pipeline

```
Government portals (PDF / HTML)
        │
        ▼
  Elastic Open Crawler / httpx fetch
        │
        ▼
  PDFParser (pdfplumber → PyPDF fallback)
        │ ParsedDocument
        ▼
  TextChunker (800 chars, 150 overlap)
        │ List[DocumentChunk]
        ▼
  EmbeddingPipeline (Jina v5 via Elastic Inference)
        │ 1024-dim vectors
        ▼
  DocumentIndexer (Elasticsearch bulk upsert)
        │
        ▼
  Index: shrammitra_labour_docs_v1
  Alias: shrammitra_labour_docs
```

---

## Elasticsearch Index Schema

| Field | Type | Notes |
|---|---|---|
| `content` | text | Main searchable text |
| `content_hi/kn/ta/te/bn` | text | Language-specific analyzers |
| `embedding` | dense_vector (1024, cosine) | Jina v5 embedding |
| `title` | text | Boosted 2.0× |
| `source_url` | keyword | For citations |
| `act_name` | keyword | Indian act name |
| `section` | keyword | Section/Rule reference |
| `doc_hash` | keyword | SHA-256 for dedup |
| `indexed_at` | date | Ingestion timestamp |

---

## Security Architecture

- **Transport**: TLS 1.2+ (nginx), HSTS enforced.
- **Webhook auth**: HMAC-SHA256 with `X-Hub-Signature-256`.
- **PII**: Phone numbers stored as `SHA-256 + SECRET_KEY` truncated to 16 chars.
- **Rate limiting**: Redis sliding window — 30 req/min per client, 1000/min global.
- **Input sanitization**: Null bytes, control chars stripped; 4096 char limit.
- **Prompt injection**: 13 compiled regex patterns detect override attempts.
- **Admin API**: JWT HS256 (60 min expiry) + bcrypt API key.
- **Dependency security**: `pip-audit` in CI pipeline.
