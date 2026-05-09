"""
Message ORM model — stores individual messages in a conversation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Message(Base):
    """Represents a single message (user or assistant) in a conversation."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # "user" or "assistant"
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    # Original user message (sanitized, no PII beyond what worker typed)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Detected language
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    # Message type: "text" | "audio" | "document"
    message_type: Mapped[str] = mapped_column(String(16), default="text")
    # WhatsApp message ID
    wa_message_id: Mapped[str | None] = mapped_column(String(256), nullable=True, unique=True)
    # RAG sources cited in the response
    sources: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Confidence score from RAG retrieval
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Number of tokens used (for cost tracking)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Latency in milliseconds
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Was this flagged by safety guardrails?
    safety_flagged: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(  # noqa: F821
        "Conversation", back_populates="messages"
    )
