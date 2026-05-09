"""
FastAPI authentication dependencies.
"""
from __future__ import annotations

import structlog
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.security import decode_access_token, verify_password

logger = structlog.get_logger(__name__)
settings = get_settings()

bearer_scheme = HTTPBearer(auto_error=True)


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> dict:
    """
    Verify JWT bearer token for admin endpoints.

    Returns the decoded token payload on success.
    Raises HTTP 401 on invalid/expired token.
    """
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("scope") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return payload
    except Exception as exc:
        logger.warning("invalid_admin_token", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> bool:
    """
    Verify raw API key for service-to-service calls.
    Uses constant-time comparison to prevent timing attacks.
    """
    if not verify_password(credentials.credentials, settings.ADMIN_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
