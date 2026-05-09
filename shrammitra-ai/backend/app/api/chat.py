"""
Direct chat query endpoint for testing and API consumers.

POST /chat/query   — admin-authenticated query
POST /chat/message — public chatbot endpoint (web UI, no auth required)
"""
from __future__ import annotations

import time

import structlog
from fastapi import APIRouter, HTTPException, Request, status

from app.agents.orchestrator import get_orchestrator
from app.middleware.auth import verify_admin_token
from app.models.schemas import ChatQueryRequest, ChatQueryResponse, SourceCitation
from fastapi import Depends

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post(
    "/query",
    response_model=ChatQueryResponse,
    summary="Direct chat query (admin)",
)
async def chat_query(
    request: ChatQueryRequest,
    _: dict = Depends(verify_admin_token),
) -> ChatQueryResponse:
    """Process a direct chat query through the full RAG pipeline (admin only)."""
    return await _run_query(request)


@router.post(
    "/message",
    response_model=ChatQueryResponse,
    summary="Public chatbot message (web UI)",
    description=(
        "Public endpoint for the web chatbot. No authentication required. "
        "Rate-limited by IP via middleware."
    ),
)
async def public_chat_message(
    request: ChatQueryRequest,
    http_request: Request,
) -> ChatQueryResponse:
    """Process a public chat message from the web UI."""
    return await _run_query(request)


async def _run_query(request: ChatQueryRequest) -> ChatQueryResponse:
    orchestrator = get_orchestrator()
    try:
        agent_response = await orchestrator.process_query(
            query=request.message,
            detected_language=request.language,
            session_id=request.session_id,
        )
    except Exception as exc:
        logger.error("chat_query_failed", error=str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "processing_failed",
                "message": "Failed to process query. Please try again.",
            },
        ) from exc

    return ChatQueryResponse(
        response=agent_response.response_text,
        language=agent_response.language,
        sources=[
            SourceCitation(
                title=s["title"],
                url=s["url"],
                excerpt=s["excerpt"],
                confidence=s["confidence"],
            )
            for s in agent_response.sources
        ],
        session_id=agent_response.session_id,
        confidence=agent_response.confidence,
        latency_ms=agent_response.latency_ms,
    )

