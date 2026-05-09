# Security Guide

## Overview

ShramMitra AI handles sensitive communications from vulnerable workers. Security is a first-class concern across all layers.

---

## Threat Model

| Threat | Mitigation |
|---|---|
| Webhook spoofing | HMAC-SHA256 `X-Hub-Signature-256` on every POST |
| PII exposure (phone numbers) | SHA-256 + SECRET_KEY hash, never stored raw |
| Prompt injection attacks | 13 compiled regex patterns, input sanitization |
| DDoS / abuse | Redis sliding window rate limiting (30/min per user) |
| Admin API unauthorized access | JWT HS256 + bcrypt API key |
| Data in transit interception | TLS 1.2+ enforced, HSTS preloaded |
| Clickjacking | `X-Frame-Options: DENY` |
| MIME sniffing | `X-Content-Type-Options: nosniff` |
| XSS via response headers | `X-XSS-Protection: 1; mode=block` |

---

## Prompt Injection Defense

The `detect_prompt_injection()` function in `backend/app/core/security.py` checks for 13 patterns:

- `ignore.*previous.*instructions`
- `forget.*instructions`
- `you are now`, `act as`, `pretend.*you`
- `DAN`, `jailbreak`, `developer mode`
- `system prompt`, `initial prompt`, `base instructions`
- `bypass.*filter`, `ignore.*guidelines`

If detected, the message is silently blocked and the worker receives a standard response.

---

## Phone Number Privacy

```python
def hash_phone_number(phone: str) -> str:
    """Never store raw phone numbers."""
    data = (phone + settings.SECRET_KEY).encode()
    return hashlib.sha256(data).hexdigest()[:16]
```

The hash is one-way. Even with database access, phone numbers cannot be recovered.

---

## Rate Limiting

Redis sliding window algorithm:

```
Global: 1000 requests/minute (all users combined)
Per client: 30 requests/minute per IP/phone
Exempt: /health, /metrics, /docs, /redoc
```

Exceeding limits returns `429 Too Many Requests` with `Retry-After` header.

---

## WhatsApp Webhook Verification

```python
def verify_whatsapp_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)  # constant-time
```

Uses `hmac.compare_digest()` to prevent timing attacks.

---

## OWASP Top 10 Compliance

| # | Risk | Status |
|---|---|---|
| A01 | Broken Access Control | JWT + bcrypt admin auth; no public admin endpoints |
| A02 | Cryptographic Failures | bcrypt for passwords; AES-256 for S3; TLS everywhere |
| A03 | Injection | Parameterized SQLAlchemy ORM; input sanitization |
| A04 | Insecure Design | Threat model documented; safety guardrails on all I/O |
| A05 | Security Misconfiguration | Docs disabled in prod; server tokens off; security headers |
| A06 | Vulnerable Components | `pip-audit` in CI |
| A07 | Auth Failures | JWT expiry 60min; no refresh tokens stored client-side |
| A08 | Software Integrity | Docker image signed; Terraform state encrypted |
| A09 | Logging | Structured JSON logs; audit log for admin actions |
| A10 | SSRF | No user-controlled URL fetching; webhook only from Meta IPs |

---

## Secrets Management

In production, secrets are stored in AWS Secrets Manager, not environment variables. The application fetches them at startup via the IAM instance role (no hardcoded credentials).

**Never commit secrets to Git.** The `.gitignore` excludes `.env` files.
