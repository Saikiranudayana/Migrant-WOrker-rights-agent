"""
Admin API endpoints.

All admin endpoints require JWT bearer authentication.

Endpoints:
- POST /admin/login — get access token
- GET  /admin/conversations — list conversations
- GET  /admin/conversations/{id} — conversation detail
- GET  /admin/sources — knowledge base sources
- POST /admin/reindex — trigger reindex
- GET  /admin/analytics — analytics summary
"""
from __future__ import annotations

import uuid
from datetime import timedelta
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.middleware.auth import verify_admin_token
from app.models.audit_log import AuditLog
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.schemas import (
    AdminLoginRequest,
    AnalyticsSummary,
    ConversationDetail,
    ConversationSummary,
    MessageSchema,
    ReindexResponse,
    SourceSchema,
    TokenResponse,
)
from app.models.source import Source
from app.rag.index_manager import IndexManager

logger = structlog.get_logger(__name__)
settings = get_settings()
router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def admin_login(request: AdminLoginRequest) -> TokenResponse:
    """
    Exchange an admin API key for a JWT access token.

    Uses constant-time comparison to prevent timing attacks.
    """
    if not verify_password(request.api_key, settings.ADMIN_API_KEY):
        logger.warning("admin_login_failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    token = create_access_token(
        data={"sub": "admin", "scope": "admin"},
        expires_delta=timedelta(minutes=60),
    )
    logger.info("admin_login_success")
    return TokenResponse(access_token=token, expires_in=3600)


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    language: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(verify_admin_token),
) -> List[ConversationSummary]:
    """List conversations with optional filtering and pagination."""
    query = select(Conversation)

    if language:
        query = query.where(Conversation.language == language)
    if state:
        query = query.where(Conversation.state == state)

    query = (
        query
        .order_by(Conversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    conversations = result.scalars().all()

    return [
        ConversationSummary(
            id=c.id,
            language=c.language,
            state=c.state,
            message_count=c.message_count,
            is_voice=c.is_voice,
            created_at=c.created_at,
            updated_at=c.updated_at,
            feedback_rating=c.feedback_rating,
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(verify_admin_token),
) -> ConversationDetail:
    """Get full conversation detail including all messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = messages_result.scalars().all()

    # Audit log the access
    db.add(AuditLog(
        actor=admin.get("sub", "admin"),
        action="conversation_viewed",
        resource_type="conversation",
        resource_id=str(conversation_id),
    ))

    return ConversationDetail(
        id=conversation.id,
        language=conversation.language,
        state=conversation.state,
        message_count=conversation.message_count,
        is_voice=conversation.is_voice,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        feedback_rating=conversation.feedback_rating,
        messages=[
            MessageSchema(
                id=m.id,
                role=m.role,
                content=m.content,
                language=m.language,
                message_type=m.message_type,
                sources=m.sources,
                confidence_score=m.confidence_score,
                tokens_used=m.tokens_used,
                latency_ms=m.latency_ms,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.get("/sources", response_model=List[SourceSchema])
async def list_sources(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(verify_admin_token),
) -> List[SourceSchema]:
    """List knowledge base sources and their sync status."""
    query = select(Source).order_by(Source.last_synced_at.desc())
    if status_filter:
        query = query.where(Source.status == status_filter)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sources = result.scalars().all()

    return [
        SourceSchema(
            id=s.id,
            url=s.url,
            title=s.title,
            source_type=s.source_type,
            status=s.status,
            chunk_count=s.chunk_count,
            language=s.language,
            last_synced_at=s.last_synced_at,
            created_at=s.created_at,
        )
        for s in sources
    ]


@router.post("/reindex", response_model=ReindexResponse)
async def trigger_reindex(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(verify_admin_token),
) -> ReindexResponse:
    """
    Trigger a full knowledge base reindex.

    This recreates the Elasticsearch index and re-ingests all sources.
    The operation runs asynchronously — use /admin/sources to monitor progress.
    """
    import asyncio
    import uuid as uuid_mod

    job_id = uuid_mod.uuid4().hex[:12]
    logger.info("reindex_triggered", job_id=job_id, actor=admin.get("sub"))

    # Audit log
    db.add(AuditLog(
        actor=admin.get("sub", "admin"),
        action="reindex_triggered",
        details={"job_id": job_id},
    ))

    # Trigger async reindex (non-blocking)
    asyncio.create_task(_run_reindex(job_id))

    return ReindexResponse(
        status="started",
        job_id=job_id,
        message="Reindex job started. Monitor progress via /admin/sources.",
    )


async def _run_reindex(job_id: str) -> None:
    """Background reindex task."""
    try:
        logger.info("reindex_job_running", job_id=job_id)
        index_manager = IndexManager()
        await index_manager.create_index(force=True)
        logger.info("reindex_job_complete", job_id=job_id)
    except Exception as exc:
        logger.error("reindex_job_failed", job_id=job_id, error=str(exc))


@router.get("/analytics", response_model=AnalyticsSummary)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(verify_admin_token),
) -> AnalyticsSummary:
    """Return analytics summary for the admin dashboard."""
    # Total conversations
    total_conv = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0
    active_conv = (
        await db.execute(
            select(func.count(Conversation.id)).where(Conversation.state == "active")
        )
    ).scalar() or 0

    # Total messages
    total_msgs = (await db.execute(select(func.count(Message.id)))).scalar() or 0

    # Language breakdown
    lang_rows = (
        await db.execute(
            select(Conversation.language, func.count(Conversation.id))
            .group_by(Conversation.language)
        )
    ).all()
    language_breakdown = {row[0]: row[1] for row in lang_rows}

    # Avg confidence and latency
    stats = (
        await db.execute(
            select(
                func.avg(Message.confidence_score),
                func.avg(Message.latency_ms),
            ).where(Message.role == "assistant")
        )
    ).one()
    avg_confidence = float(stats[0] or 0.0)
    avg_latency = float(stats[1] or 0.0)

    # Voice messages
    voice_count = (
        await db.execute(
            select(func.count(Conversation.id)).where(Conversation.is_voice.is_(True))
        )
    ).scalar() or 0

    # Avg feedback rating
    rating = (
        await db.execute(
            select(func.avg(Conversation.feedback_rating))
            .where(Conversation.feedback_rating.isnot(None))
        )
    ).scalar()

    return AnalyticsSummary(
        total_conversations=total_conv,
        active_conversations=active_conv,
        total_messages=total_msgs,
        language_breakdown=language_breakdown,
        avg_confidence=round(avg_confidence, 3),
        avg_latency_ms=round(avg_latency, 1),
        voice_message_count=voice_count,
        feedback_avg_rating=round(float(rating), 2) if rating else None,
    )
