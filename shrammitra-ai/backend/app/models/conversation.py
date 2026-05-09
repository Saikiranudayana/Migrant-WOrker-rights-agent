"""
Conversation ORM model — tracks WhatsApp conversation sessions.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Conversation(Base):
    """Represents a single conversation session with a worker."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Hashed phone number — never store raw phone numbers
    phone_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Detected language code (en, hi, kn, ta, te, bn, or)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    # Conversation state (active, closed, escalated)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    # Total messages in this conversation
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    # WhatsApp message IDs for deduplication
    last_wa_message_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # Worker rating (1-5, optional)
    feedback_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_voice: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        "Message", back_populates="conversation", lazy="dynamic"
    )
