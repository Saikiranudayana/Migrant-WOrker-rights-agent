# Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- AWS account with Bedrock access (us-east-1), S3, Transcribe, Polly
- Elasticsearch 9.x cloud cluster (or self-hosted)
- Meta WhatsApp Business account with Cloud API access
- Domain name with DNS control (for production TLS)

---

## Local Development

### 1. Clone and configure

```bash
git clone https://github.com/your-org/shrammitra-ai.git
cd shrammitra-ai
cp .env.example .env
# Edit .env with your real keys
```

### 2. Start all services

```bash
make dev
# or
docker compose up -d
```

Services:
- Backend API: http://localhost:8000
- Frontend admin: http://localhost:3000
- Kibana: http://localhost:5601
- Elasticsearch: http://localhost:9200

### 3. Create Elasticsearch index

```bash
make create-index
```

### 4. Run ingestion pipeline

```bash
make ingest
# or to test with 3 sources:
python -m ingestion.sync_jobs.run_sync --limit 3
```

---

## AWS Production Deployment

### 1. Bootstrap Terraform state

```bash
# Create S3 bucket and DynamoDB table for state
aws s3 mb s3://shrammitra-tfstate --region us-east-1
aws dynamodb create-table \
  --table-name shrammitra-tflock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 2. Apply Terraform

```bash
cd infrastructure/terraform
terraform init
terraform plan -var="db_password=$DB_PASSWORD"
terraform apply -var="db_password=$DB_PASSWORD"
```

### 3. Configure secrets in AWS Secrets Manager

```bash
aws secretsmanager create-secret \
  --name shrammitra/prod \
  --secret-string '{"SECRET_KEY":"...","WHATSAPP_ACCESS_TOKEN":"...","JINA_API_KEY":"..."}'
```

### 4. Push Docker images to ECR

Handled automatically by GitHub Actions on push to `production` branch. See [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml).

### 5. Configure WhatsApp webhook

In Meta Developer Console:
- Callback URL: `https://your-domain.com/webhook/whatsapp`
- Verify token: value from `WHATSAPP_VERIFY_TOKEN` env var
- Subscribed fields: `messages`

---

## Environment Variables Reference

See [`.env.example`](../.env.example) for all variables with descriptions.

Critical variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | 32+ char random string for JWT signing |
| `DATABASE_URL` | PostgreSQL connection string |
| `ELASTICSEARCH_URL` | Elasticsearch endpoint |
| `ELASTICSEARCH_API_KEY` | Elasticsearch API key |
| `WHATSAPP_APP_SECRET` | From Meta app dashboard |
| `WHATSAPP_ACCESS_TOKEN` | Meta Cloud API permanent token |
| `AWS_DEFAULT_REGION` | Must be `us-east-1` for Bedrock |
| `JINA_API_KEY` | Fallback if Elastic Inference unavailable |

---

## Health Checks

```bash
# API health
curl https://your-domain.com/health

# Expected response
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy", "latency_ms": 2},
    "redis": {"status": "healthy", "latency_ms": 1},
    "elasticsearch": {"status": "healthy", "latency_ms": 15}
  }
}
```

---

## Zero-Downtime Reindexing

```bash
# Via Makefile
make reindex

# Or via admin API
curl -X POST https://your-domain.com/admin/reindex \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

The index manager creates a new versioned index (`_v2`), then atomically swaps the alias. No downtime.
