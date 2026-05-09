# ShramMitra AI 🤝

> **Multilingual WhatsApp AI Assistant for Migrant Worker Rights in Bengaluru**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-9.x-yellow.svg)](https://elastic.co)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)

---

## Problem Statement

Millions of migrant workers in Bengaluru — construction workers, gig workers, domestic workers, contract labourers — face violations of their fundamental labour rights every day. Critical information about PF, ESI, minimum wages, complaint procedures, and welfare schemes exists in official government portals, but is:

- Written in English only
- Buried inside complex PDFs
- Impossible to navigate on a smartphone
- Completely inaccessible to workers speaking Hindi, Bengali, Odia, Tamil, Telugu, or Kannada

**Result:** Workers cannot access the rights they are legally entitled to.

---

## Solution Overview

ShramMitra AI ("Friend of the Worker" in Hindi) is a production-ready, multilingual WhatsApp chatbot that:

1. Accepts messages in 7 languages via WhatsApp
2. Detects the worker's language automatically
3. Searches a verified knowledge base of official labour law documents using RAG
4. Generates a clear, simple, source-cited response in the worker's language
5. Guides workers through complaint filing, helpline numbers, and welfare schemes
6. Supports voice messages (STT/TTS) for workers who cannot type

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WORKER                                      │
│              Sends WhatsApp message in their language               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  WhatsApp Business  │
                    │       API           │
                    └──────────┬──────────┘
                               │ HTTPS Webhook
                    ┌──────────▼──────────┐
                    │   AWS API Gateway   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   FastAPI Backend   │
                    │  Auth + Rate Limit  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
   ┌──────────▼─────┐ ┌────────▼──────┐ ┌──────▼──────────┐
   │ Lang Detection │ │ Session Mgmt  │ │  Audio (STT/TTS) │
   │  (Bedrock/ES)  │ │   (Redis)     │ │   (Transcribe)   │
   └──────────┬─────┘ └───────────────┘ └─────────────────┘
              │
   ┌──────────▼──────────────────────────┐
   │       AgentCore Orchestrator        │
   │   ┌─────────────────────────────┐   │
   │   │   Elastic Agent Builder     │   │
   │   └─────────────────────────────┘   │
   └──────────┬──────────────────────────┘
              │
   ┌──────────▼──────────┐
   │    RAG Retrieval     │
   │  ┌───────────────┐  │
   │  │ Elasticsearch │  │
   │  │  + Jina v5    │  │
   │  │  Embeddings   │  │
   │  └───────────────┘  │
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │   Amazon Bedrock    │
   │  (Claude 3 Sonnet)  │
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │  Safety Guardrails  │
   │  + Disclaimer Layer │
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │   WhatsApp Reply    │
   └─────────────────────┘

INGESTION PIPELINE (Separate):
Open Crawler → Official Sites → PDF Parser → Chunker → Jina v5 Embeddings → Elasticsearch
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Amazon Bedrock (Claude 3 Sonnet / Claude 3 Haiku) |
| **Vector Store** | Elasticsearch 9.x with Jina v5 multilingual embeddings |
| **Crawler** | Elastic Open Crawler |
| **Agent Framework** | AgentCore + Elastic Agent Builder |
| **Backend** | Python 3.11, FastAPI, Redis |
| **Frontend** | Next.js 14, TailwindCSS, shadcn/ui |
| **Database** | PostgreSQL 15 |
| **Messaging** | WhatsApp Business API (Meta Cloud API) |
| **Voice** | Amazon Transcribe (STT), Amazon Polly (TTS) |
| **Infrastructure** | AWS EC2, API Gateway, S3, CloudWatch, Secrets Manager, IAM |
| **IaC** | Terraform |
| **Containers** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |

---

## Supported Languages

| Language | Script | Code |
|---|---|---|
| English | Latin | `en` |
| Hindi | Devanagari | `hi` |
| Kannada | Kannada script | `kn` |
| Tamil | Tamil script | `ta` |
| Telugu | Telugu script | `te` |
| Bengali | Bengali script | `bn` |
| Odia | Odia script | `or` |

---

## Features

### Core Features
- 🌐 **7-Language Support** — Automatic detection + native-language responses
- 📚 **RAG Knowledge Base** — Grounded in official government sources only
- 📱 **WhatsApp Integration** — Works on any smartphone with WhatsApp
- 🎤 **Voice Support** — Speech-to-text and text-to-speech for audio messages
- 📋 **Complaint Navigation** — Step-by-step guidance for filing complaints
- 🔒 **Privacy-First** — Minimal data collection, no unnecessary PII storage

### Knowledge Coverage
- Karnataka Shops & Establishments Act
- Payment of Wages Act
- Minimum Wages Act
- Employees' Provident Fund (EPFO)
- Employees' State Insurance (ESIC)
- Building & Construction Workers Act
- Interstate Migrant Workmen Act
- Karnataka Labour Department notifications
- Welfare board schemes for migrant workers

### Admin Dashboard
- 📊 Conversation analytics and language breakdown
- 📝 Conversation logs with search
- 🔄 Knowledge base sync status
- 🕷️ Crawler status and scheduling
- ❤️ System health monitoring
- 🚨 Alert management

---

## Project Structure

```
shrammitra-ai/
├── backend/
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── agents/         # AgentCore + Elastic agent definitions
│   │   ├── rag/            # RAG retrieval pipeline
│   │   ├── services/       # WhatsApp, voice, language services
│   │   ├── models/         # Pydantic models & DB models
│   │   ├── middleware/      # Auth, rate limiting, logging
│   │   ├── core/           # Config, security, DB connection
│   │   ├── utils/          # Helpers and formatters
│   │   └── main.py         # FastAPI app entry point
│   ├── tests/              # Unit, integration, API, security tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Next.js admin dashboard
│   ├── app/
│   ├── components/
│   └── services/
├── ingestion/              # Data ingestion pipeline
│   ├── crawler/            # Open Crawler config
│   ├── pdf_parser/         # PDF extraction
│   ├── chunking/           # Text chunking strategies
│   ├── embeddings/         # Jina v5 embedding generation
│   └── sync_jobs/          # Scheduled sync jobs
├── infrastructure/
│   ├── terraform/          # AWS infrastructure as code
│   ├── docker/             # Docker configurations
│   ├── nginx/              # Reverse proxy config
│   └── monitoring/         # CloudWatch dashboards
├── docs/                   # Full documentation
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- AWS Account with Bedrock access
- Elastic Cloud account (or self-hosted Elasticsearch 9.x)
- WhatsApp Business API credentials (Meta Developer Portal)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/shrammitra-ai.git
cd shrammitra-ai
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
nano .env
```

### 3. Local Development with Docker

```bash
# Start all services
make dev

# Or manually
docker compose up --build
```

### 4. Run Ingestion Pipeline

```bash
# Crawl official sites and build knowledge base
make ingest

# Or manually
cd ingestion && python sync_jobs/run_sync.py
```

### 5. Access the Dashboard

- Admin Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## Local Development Guide

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Dashboard at http://localhost:3000
```

### Running Tests

```bash
# All tests
make test

# Backend only
cd backend && pytest tests/ -v --cov=app --cov-report=html

# Specific test suite
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/security/ -v
```

---

## Docker Setup

```bash
# Build all images
docker compose build

# Start all services (backend, frontend, postgres, redis, elasticsearch)
docker compose up -d

# View logs
docker compose logs -f backend

# Stop all services
docker compose down
```

### Services

| Service | Port | Description |
|---|---|---|
| `backend` | 8000 | FastAPI application |
| `frontend` | 3000 | Next.js dashboard |
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Session & cache store |
| `elasticsearch` | 9200 | Vector search engine |
| `kibana` | 5601 | Elasticsearch UI |
| `nginx` | 80/443 | Reverse proxy |

---

## Terraform Deployment

```bash
cd infrastructure/terraform

# Initialize
terraform init

# Plan
terraform plan -var-file=environments/production.tfvars

# Apply
terraform apply -var-file=environments/production.tfvars
```

### What Terraform provisions

- VPC with public/private subnets
- EC2 instance (t3.medium) for backend
- Application Load Balancer
- RDS PostgreSQL instance
- ElastiCache Redis cluster
- S3 buckets (documents, audio, backups)
- API Gateway for WhatsApp webhook
- CloudWatch dashboards and alarms
- IAM roles with least privilege
- Secrets Manager for credentials
- Security Groups and NACLs

---

## Environment Variables

See [.env.example](.env.example) for the full list. Key variables:

```env
# AWS
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Elasticsearch
ELASTICSEARCH_URL=https://your-cluster.es.io:443
ELASTICSEARCH_API_KEY=...
ELASTICSEARCH_INDEX_NAME=shrammitra_labour_docs

# WhatsApp
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_VERIFY_TOKEN=...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/shrammitra

# Security
SECRET_KEY=...  # 32+ char random string
API_KEY_HASH=...
```

---

## WhatsApp API Setup

1. Go to [Meta Developer Portal](https://developers.facebook.com)
2. Create a new app → Business → WhatsApp
3. Add WhatsApp product
4. Generate a permanent access token
5. Configure webhook URL: `https://your-domain.com/webhook/whatsapp`
6. Verify token: set in `.env` as `WHATSAPP_VERIFY_TOKEN`
7. Subscribe to: `messages`, `message_deliveries`, `message_reads`

See [docs/whatsapp-setup.md](docs/whatsapp-setup.md) for detailed instructions.

---

## AWS Setup

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Enable Bedrock model access
aws bedrock put-foundation-model-entitlement \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --region ap-south-1
```

See [docs/deployment.md](docs/deployment.md) for full AWS setup.

---

## Elastic Setup

```bash
# Create Elasticsearch index with multilingual mapping
cd backend
python -c "from app.rag.index_manager import create_index; import asyncio; asyncio.run(create_index())"

# Verify index
curl -X GET "https://your-cluster.es.io:443/shrammitra_labour_docs" \
  -H "Authorization: ApiKey YOUR_API_KEY"
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/webhook/whatsapp` | WhatsApp webhook (incoming messages) |
| `GET` | `/webhook/whatsapp` | Webhook verification |
| `POST` | `/chat/query` | Direct chat query (for testing) |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/admin/conversations` | List conversations (auth required) |
| `GET` | `/admin/conversations/{id}` | Conversation detail |
| `GET` | `/admin/sources` | Knowledge base sources |
| `POST` | `/admin/reindex` | Trigger reindex |
| `GET` | `/admin/analytics` | Analytics summary |

Full API docs: http://localhost:8000/docs

---

## Demo Workflow

### Worker in Hindi:
```
Worker: "Mera malik overtime ka paisa nahi de raha"
ShramMitra: "आपका मालिक आपको ओवरटाइम का वेतन देने के लिए कानूनी रूप से बाध्य है।
             मजदूरी भुगतान अधिनियम, 1936 के अनुसार...
             📞 श्रम विभाग हेल्पलाइन: 1800-425-1200 (निःशुल्क)"
```

### Worker in Tamil:
```
Worker: "எனக்கு PF கிடைக்கவில்லை"
ShramMitra: "உங்கள் PF பற்றிய புகாரை EPFO-வில் பதிவு செய்யலாம்.
             📱 EPFO UAN போர்டல்: https://unifiedportal-mem.epfindia.gov.in
             📞 EPFO Helpline: 1800-118-005"
```

---

## Monitoring

- CloudWatch Dashboard: AWS Console → CloudWatch → Dashboards → ShramMitra
- Application Metrics: http://localhost:8000/metrics (Prometheus format)
- Kibana: http://localhost:5601 (Elasticsearch visualization)
- Admin Dashboard: http://localhost:3000/admin

---

## Security Practices

- All secrets in AWS Secrets Manager / environment variables (never in code)
- HTTPS enforced everywhere via nginx + Let's Encrypt
- WhatsApp webhook signature verification (HMAC-SHA256)
- JWT-based admin authentication with RBAC
- Rate limiting: 30 req/min per phone number
- Input sanitization to prevent prompt injection
- Audit logging for all admin actions
- No PII stored beyond phone number hash
- See [docs/security.md](docs/security.md) for full details

---

## Legal Disclaimer

> **ShramMitra AI provides informational guidance only and is not legal counsel. The information provided is based on publicly available official government sources and should not be construed as legal advice. For specific legal issues, please consult a qualified labour lawyer or contact the official Karnataka Labour Department.**

---

## Future Enhancements

- [ ] IVR/phone call support (Amazon Connect)
- [ ] Telegram bot channel
- [ ] Offline SMS fallback (basic feature phone support)
- [ ] Document upload (wage slips, appointment letters) for case analysis
- [ ] Integration with Karnataka e-Labour portal for direct complaint filing
- [ ] NGO partner portal for case management
- [ ] Worker mobile app (React Native)
- [ ] Chatbot for 10 additional Indian languages

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/developer-guide.md](docs/developer-guide.md).

---

## Acknowledgements

- Karnataka Labour Department for public data sources
- Elastic for Elasticsearch and Jina v5 embeddings
- AWS for Bedrock and cloud infrastructure
- Meta for WhatsApp Business API
- All labour rights organizations working for migrant workers in Bengaluru

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ for India's migrant workers.*
