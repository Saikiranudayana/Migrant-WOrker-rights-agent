"""
Source ORM model — tracks knowledge base documents and their sync status.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Source(Base):
    """Represents a knowledge base source document or website."""

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Source URL or file path
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    # "website" | "pdf" | "notification" | "circular"
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="website")
    # "active" | "error" | "pending"
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    # Number of chunks indexed in Elasticsearch
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    # Error message if status == "error"
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Language of the source content
    language: Mapped[str] = mapped_column(String(8), default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
