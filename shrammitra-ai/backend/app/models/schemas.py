"""
Pydantic schemas for API request/response validation.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── WhatsApp Webhook Schemas ──────────────────────────────────────────────────

class WATextMessage(BaseModel):
    body: str


class WAAudioMessage(BaseModel):
    id: str
    mime_type: str


class WAMessage(BaseModel):
    id: str
    from_: str = Field(alias="from")
    timestamp: str
    type: str
    text: Optional[WATextMessage] = None
    audio: Optional[WAAudioMessage] = None

    model_config = {"populate_by_name": True}


class WAContact(BaseModel):
    profile: dict[str, Any]
    wa_id: str


class WAValue(BaseModel):
    messaging_product: str
    metadata: dict[str, Any]
    contacts: Optional[List[WAContact]] = None
    messages: Optional[List[WAMessage]] = None
    statuses: Optional[List[dict]] = None


class WAChange(BaseModel):
    value: WAValue
    field: str


class WAEntry(BaseModel):
    id: str
    changes: List[WAChange]


class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[WAEntry]


# ── Chat Query Schemas ────────────────────────────────────────────────────────

class ChatQueryRequest(BaseModel):
    """Direct chat query for testing purposes."""
    message: str = Field(min_length=1, max_length=4096)
    language: Optional[str] = Field(default=None, pattern="^(en|hi|kn|ta|te|bn|or)$")
    session_id: Optional[str] = Field(default=None, max_length=128)

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only.")
        return v.strip()


class SourceCitation(BaseModel):
    title: str
    url: str
    excerpt: str
    confidence: float


class ChatQueryResponse(BaseModel):
    """Response from the chat query endpoint."""
    response: str
    language: str
    sources: List[SourceCitation]
    session_id: str
    confidence: float
    disclaimer: str = (
        "This assistant provides informational guidance only and is not legal counsel."
    )
    latency_ms: int


# ── Admin Schemas ─────────────────────────────────────────────────────────────

class ConversationSummary(BaseModel):
    id: UUID
    language: str
    state: str
    message_count: int
    is_voice: bool
    created_at: datetime
    updated_at: datetime
    feedback_rating: Optional[int]


class ConversationDetail(ConversationSummary):
    messages: List["MessageSchema"]


class MessageSchema(BaseModel):
    id: UUID
    role: str
    content: str
    language: str
    message_type: str
    sources: Optional[list]
    confidence_score: Optional[float]
    tokens_used: Optional[int]
    latency_ms: Optional[int]
    created_at: datetime


class SourceSchema(BaseModel):
    id: UUID
    url: str
    title: str
    source_type: str
    status: str
    chunk_count: int
    language: str
    last_synced_at: Optional[datetime]
    created_at: datetime


class AnalyticsSummary(BaseModel):
    total_conversations: int
    active_conversations: int
    total_messages: int
    language_breakdown: dict[str, int]
    avg_confidence: float
    avg_latency_ms: float
    voice_message_count: int
    feedback_avg_rating: Optional[float]


class ReindexResponse(BaseModel):
    status: str
    job_id: str
    message: str


# ── Auth Schemas ──────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminLoginRequest(BaseModel):
    api_key: str = Field(min_length=16, max_length=512)


# ── Health Schemas ────────────────────────────────────────────────────────────

class ServiceStatus(BaseModel):
    status: str  # "ok" | "degraded" | "down"
    latency_ms: Optional[float]
    details: Optional[str]


class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    version: str
    environment: str
    services: dict[str, ServiceStatus]
    timestamp: datetime
