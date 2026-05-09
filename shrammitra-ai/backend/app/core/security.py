"""
Security utilities: JWT, password hashing, API key validation,
prompt injection detection, and input sanitization.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Constants ─────────────────────────────────────────────────────────────────
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Prompt injection patterns to detect and block
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(if\s+you\s+are|a)",
    r"new\s+instructions",
    r"system\s+prompt",
    r"forget\s+(your|all|previous)",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
    r"override\s+(your|the)\s+instructions",
    r"<\s*script",
    r"javascript:",
    r"\bexec\b.*\bsh\b",
    r"\bdrop\s+table\b",
]

COMPILED_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS
]


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def verify_whatsapp_signature(payload: bytes, signature_header: str) -> bool:
    """
    Verify WhatsApp webhook payload using HMAC-SHA256.

    Meta sends: X-Hub-Signature-256: sha256=<hex_digest>
    """
    if not signature_header.startswith("sha256="):
        return False
    expected_sig = signature_header[len("sha256="):]
    computed_sig = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed_sig, expected_sig)


def hash_phone_number(phone_number: str) -> str:
    """
    One-way hash a phone number for privacy-safe storage.

    We never store raw phone numbers beyond the session.
    """
    return hashlib.sha256(
        (phone_number + settings.SECRET_KEY).encode()
    ).hexdigest()[:16]


def sanitize_input(text: str, max_length: int = 4096) -> str:
    """
    Sanitize user input:
    - Truncate to max_length
    - Strip null bytes
    - Remove control characters except newlines and tabs
    """
    if not text:
        return ""
    # Truncate
    text = text[:max_length]
    # Strip null bytes
    text = text.replace("\x00", "")
    # Remove non-printable control characters except \n and \t
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()


def detect_prompt_injection(text: str) -> bool:
    """
    Detect potential prompt injection attempts in user input.

    Returns True if injection is detected.
    """
    if not text:
        return False
    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(
                "prompt_injection_detected",
                pattern=pattern.pattern,
                text_preview=text[:100],
            )
            return True
    return False


def generate_request_id() -> str:
    """Generate a cryptographically secure request ID."""
    return secrets.token_urlsafe(16)
