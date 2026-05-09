"""
Session service — manages conversation context in Redis.

Stores:
- Current conversation language
- Recent message history (last 10 turns) for context window
- Session state machine (greeting, active, complaint_flow, etc.)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog

from app.core.config import get_settings
from app.core.redis_client import get_redis_client
from app.core.security import hash_phone_number

logger = structlog.get_logger(__name__)
settings = get_settings()

MAX_HISTORY_TURNS = 10


class SessionService:
    """Redis-backed session manager for WhatsApp conversations."""

    async def get_session(self, phone_number: str) -> dict[str, Any]:
        """
        Retrieve or create a session for a phone number.

        Returns session dict with:
        - session_id: hashed phone number identifier
        - language: detected language code
        - state: conversation state
        - history: list of recent {role, content} dicts
        - created_at: ISO timestamp
        """
        redis = await get_redis_client()
        session_id = hash_phone_number(phone_number)
        key = f"session:{session_id}"

        data = await redis.get(key)
        if data:
            session = json.loads(data)
            # Refresh TTL on access
            await redis.expire(key, settings.SESSION_TTL_SECONDS)
            return session

        # New session
        session: dict[str, Any] = {
            "session_id": session_id,
            "language": settings.DEFAULT_LANGUAGE,
            "state": "greeting",
            "history": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await redis.setex(key, settings.SESSION_TTL_SECONDS, json.dumps(session))
        logger.info("session_created", session_id=session_id)
        return session

    async def update_session(
        self,
        phone_number: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Update session fields and persist to Redis."""
        redis = await get_redis_client()
        session_id = hash_phone_number(phone_number)
        key = f"session:{session_id}"

        session = await self.get_session(phone_number)
        session.update(updates)
        await redis.setex(key, settings.SESSION_TTL_SECONDS, json.dumps(session))
        return session

    async def add_to_history(
        self,
        phone_number: str,
        role: str,
        content: str,
    ) -> None:
        """Append a message to the conversation history (capped at MAX_HISTORY_TURNS)."""
        session = await self.get_session(phone_number)
        history: list = session.get("history", [])
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Keep only the last N turns (user + assistant pairs)
        if len(history) > MAX_HISTORY_TURNS * 2:
            history = history[-(MAX_HISTORY_TURNS * 2):]
        await self.update_session(phone_number, {"history": history})

    async def get_history(self, phone_number: str) -> list[dict[str, str]]:
        """Return formatted message history for LLM context."""
        session = await self.get_session(phone_number)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in session.get("history", [])
        ]

    async def clear_session(self, phone_number: str) -> None:
        """Delete a session (e.g., when conversation ends or worker resets)."""
        redis = await get_redis_client()
        session_id = hash_phone_number(phone_number)
        await redis.delete(f"session:{session_id}")
        logger.info("session_cleared", session_id=session_id)

    async def check_duplicate_message(self, wa_message_id: str) -> bool:
        """
        Check if a WhatsApp message ID has already been processed.

        WhatsApp can deliver duplicates; this prevents double-processing.
        Returns True if it's a duplicate (already seen).
        """
        redis = await get_redis_client()
        key = f"processed_msg:{wa_message_id}"
        was_set = await redis.setnx(key, "1")
        if was_set:
            # First time seeing this message — mark and expire after 24h
            await redis.expire(key, 86400)
            return False
        return True  # Duplicate


_session_service: SessionService | None = None


def get_session_service() -> SessionService:
    """Return singleton SessionService instance."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
