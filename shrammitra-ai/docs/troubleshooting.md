# Troubleshooting

## Backend

### `ConnectionRefusedError: Redis`

- Check Redis is running: `docker compose ps redis`
- Check `REDIS_URL` in `.env`
- Test: `redis-cli -u $REDIS_URL ping`

### `elasticsearch.ConnectionError`

- Check ES is running: `curl http://localhost:9200/_cluster/health`
- If using Elastic Cloud, verify `ELASTICSEARCH_URL` includes `https://` and `ELASTICSEARCH_API_KEY` is set.
- Check ES logs: `docker compose logs elasticsearch`

### `botocore.exceptions.NoCredentialsError`

- Ensure AWS credentials are set in `.env` or via IAM instance profile.
- Test: `aws bedrock list-foundation-models --region us-east-1`
- Bedrock must be enabled in your AWS account for `us-east-1`.

### WhatsApp webhook returns 403

- `X-Hub-Signature-256` mismatch. Verify `WHATSAPP_APP_SECRET` in `.env` matches the value in Meta Developer Console → App Settings → App Secret.
- Test signature locally: `make dev` then use ngrok to expose `localhost:8000`.

### Rate limit hit during testing

Exempt your test IP or increase `RATE_LIMIT_PER_CLIENT_RPM` in `.env` for dev:
```
RATE_LIMIT_PER_CLIENT_RPM=1000
```

---

## Ingestion Pipeline

### `pdf_parser: empty content`

- The PDF may be scanned (image-only). pdfplumber cannot extract text from image PDFs. Consider adding Tesseract OCR as a fallback.
- Check: `pdfplumber.open("file.pdf").pages[0].extract_text()`

### `bulk_index_errors`

- Check Elasticsearch index mapping: `GET shrammitra_labour_docs_v1/_mapping`
- Ensure embedding dimension is 1024. Mismatches cause bulk rejection.
- Check available disk space on ES node.

### Jina v5 inference endpoint not found

- Create the inference endpoint first:
  ```bash
  curl -X PUT "http://localhost:9200/_inference/text_embedding/jina-embeddings-v3" \
    -H "Content-Type: application/json" \
    -d '{"service":"jinaai","service_settings":{"api_key":"$JINA_API_KEY","model_id":"jina-embeddings-v3"}}'
  ```

---

## Frontend

### `NEXT_PUBLIC_API_URL` not picked up

- This variable must be set at **build time**, not runtime.
- For Docker, pass it as a build arg: `docker build --build-arg NEXT_PUBLIC_API_URL=https://api.example.com .`
- Or set it in `docker-compose.yml` under `frontend.environment`.

### Admin dashboard shows "Failed to load analytics"

- Confirm backend is running: `curl http://localhost:8000/health`
- Confirm admin token is stored in `localStorage.shrammitra_token`.
- Check browser console for CORS errors — ensure `CORS_ORIGINS` includes the frontend URL.

---

## CI/CD

### Docker build fails in GitHub Actions

- Check ECR repository exists and `secrets.ECR_REGISTRY` is set in repository secrets.
- Ensure `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` have ECR push permissions.

### Tests fail with `ModuleNotFoundError`

- The `backend/` directory must be in `PYTHONPATH`. Add to pytest command:
  ```
  PYTHONPATH=backend pytest backend/tests/
  ```
  or use `pyproject.toml` / `pytest.ini` `pythonpath` setting.
