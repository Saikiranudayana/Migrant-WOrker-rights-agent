"""
Utility: log conversation messages to the database.

This is called from the webhook handler to persist conversations
for analytics and admin review.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

import structlog
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_phone_number
from app.models.conversation import Conversation
from app.models.message import Message

logger = structlog.get_logger(__name__)


async def log_conversation_message(
    phone_number: str,
    user_message: str,
    assistant_response: str,
    language: str,
    sources: List[dict],
    confidence: float,
    tokens_used: int,
    latency_ms: int,
    wa_message_id: str,
    is_voice: bool = False,
) -> None:
    """
    Persist a conversation exchange to PostgreSQL.

    Uses a separate DB session to avoid blocking the webhook response.
    Phone numbers are hashed before storage.
    """
    phone_hash = hash_phone_number(phone_number)

    try:
        async with AsyncSessionLocal() as session:
            # Get or create conversation
            result = await session.execute(
                select(Conversation)
                .where(Conversation.phone_hash == phone_hash)
                .where(Conversation.state == "active")
                .order_by(Conversation.created_at.desc())
                .limit(1)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                conversation = Conversation(
                    phone_hash=phone_hash,
                    language=language,
                    state="active",
                    is_voice=is_voice,
                )
                session.add(conversation)
                await session.flush()

            # Update conversation metadata
            conversation.language = language
            conversation.message_count += 2  # user + assistant
            conversation.last_wa_message_id = wa_message_id
            if is_voice:
                conversation.is_voice = True

            # Add user message
            user_msg = Message(
                conversation_id=conversation.id,
                role="user",
                content=user_message[:4096],
                language=language,
                message_type="audio" if is_voice else "text",
                wa_message_id=wa_message_id,
            )
            session.add(user_msg)

            # Add assistant message
            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=assistant_response[:4096],
                language=language,
                message_type="text",
                sources=sources if sources else None,
                confidence_score=confidence,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
            )
            session.add(assistant_msg)

            await session.commit()
            logger.info("conversation_logged", conversation_id=str(conversation.id))

    except Exception as exc:
        logger.error("conversation_logging_failed", error=str(exc), exc_info=True)
        # Don't re-raise — logging failure should not affect the user experience
