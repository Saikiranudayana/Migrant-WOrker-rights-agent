"""
Audit log ORM model — immutable log of admin actions.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """Immutable audit trail for all admin actions."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Admin user identifier
    actor: Mapped[str] = mapped_column(String(256), nullable=False)
    # Action performed (e.g., "reindex_triggered", "conversation_viewed")
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # Target resource
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # Additional context
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Client IP (anonymized to /24 subnet)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
