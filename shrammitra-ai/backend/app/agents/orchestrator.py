"""
AgentCore Orchestrator — the central intelligence coordinator for ShramMitra AI.

Orchestrates the full pipeline:
1. Input validation + safety check
2. Language detection
3. RAG retrieval from Elasticsearch
4. Context sufficiency validation
5. LLM generation via Amazon Bedrock
6. Output safety guardrails
7. Response formatting for WhatsApp

This is the single entry point for all query processing.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import List, Optional

import structlog

from app.agents.bedrock_client import get_bedrock_client
from app.agents.safety_guardrail import DISCLAIMER, get_safety_guardrail
from app.core.config import get_settings
from app.rag.retriever import RetrievedChunk, get_rag_retriever
from app.services.language_service import detect_language

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass
class AgentResponse:
    """Structured response from the AgentCore orchestrator."""
    response_text: str
    language: str
    sources: List[dict]
    confidence: float
    tokens_used: int
    latency_ms: int
    session_id: str
    was_blocked: bool = False
    block_reason: Optional[str] = None


class AgentCoreOrchestrator:
    """
    Central orchestrator for ShramMitra AI.

    Implements the Elastic Agent Builder pattern:
    - Tool selection (RAG retrieval as primary tool)
    - Context assembly
    - LLM invocation
    - Response post-processing
    """

    def __init__(self) -> None:
        self._retriever = get_rag_retriever()
        self._bedrock = get_bedrock_client()
        self._guardrail = get_safety_guardrail()

    async def process_query(
        self,
        query: str,
        phone_number: str | None = None,
        session_id: str | None = None,
        conversation_history: List[dict] | None = None,
        detected_language: str | None = None,
    ) -> AgentResponse:
        """
        Process a worker's query through the full RAG + LLM pipeline.

        Args:
            query: Worker's message (any supported language)
            phone_number: Worker's phone number (for session tracking)
            session_id: Existing session ID or None to create new
            conversation_history: Recent conversation turns
            detected_language: Pre-detected language (optional override)

        Returns:
            AgentResponse with the generated reply and metadata
        """
        start_time = time.monotonic()
        session_id = session_id or uuid.uuid4().hex[:12]

        structlog.contextvars.bind_contextvars(session_id=session_id)
        logger.info("agent_processing_query", query_length=len(query))

        # ── Step 1: Language Detection ────────────────────────────────────────
        if detected_language and detected_language in settings.SUPPORTED_LANGUAGES:
            language = detected_language
            lang_confidence = 1.0
        else:
            language, lang_confidence = detect_language(query)
        logger.info("language_detected", language=language, confidence=lang_confidence)

        # ── Step 2: Input Safety Guardrail ────────────────────────────────────
        guardrail_result = self._guardrail.validate_input(query, language)
        if not guardrail_result.is_safe:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            logger.warning(
                "query_blocked_by_guardrail",
                reason=guardrail_result.blocked_reason,
            )
            return AgentResponse(
                response_text=guardrail_result.suggested_response or "",
                language=language,
                sources=[],
                confidence=0.0,
                tokens_used=0,
                latency_ms=latency_ms,
                session_id=session_id,
                was_blocked=True,
                block_reason=guardrail_result.blocked_reason,
            )

        clean_query = guardrail_result.sanitized_input

        # ── Step 3: RAG Retrieval ─────────────────────────────────────────────
        chunks: List[RetrievedChunk] = await self._retriever.retrieve(
            query=clean_query,
            language=language,
            top_k=settings.RAG_TOP_K,
        )

        # ── Step 4: Context Sufficiency Check ─────────────────────────────────
        has_context, fallback_response = self._guardrail.validate_context(
            chunks, language
        )

        if not has_context:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResponse(
                response_text=self._guardrail.apply_output_guardrails(
                    fallback_response or "", language
                ),
                language=language,
                sources=[],
                confidence=0.0,
                tokens_used=0,
                latency_ms=latency_ms,
                session_id=session_id,
            )

        # ── Step 5: Context Assembly ──────────────────────────────────────────
        context_text = self._retriever.format_context(chunks)
        citations = self._retriever.extract_citations(chunks)
        avg_confidence = sum(c.score for c in chunks) / len(chunks)

        # ── Step 6: LLM Generation via Amazon Bedrock ─────────────────────────
        raw_response, tokens_used = await self._bedrock.generate(
            user_message=clean_query,
            context=context_text,
            language=language,
            conversation_history=conversation_history or [],
        )

        # ── Step 7: Output Safety + Formatting ────────────────────────────────
        final_response = self._guardrail.apply_output_guardrails(raw_response, language)

        latency_ms = int((time.monotonic() - start_time) * 1000)

        logger.info(
            "agent_response_complete",
            language=language,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            citations=len(citations),
            confidence=avg_confidence,
        )

        return AgentResponse(
            response_text=final_response,
            language=language,
            sources=citations,
            confidence=avg_confidence,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            session_id=session_id,
        )

    async def process_voice_query(
        self,
        audio_bytes: bytes,
        phone_number: str,
        session_id: str | None = None,
        conversation_history: List[dict] | None = None,
    ) -> tuple[AgentResponse, str]:
        """
        Process a voice message:
        1. STT → text
        2. process_query() on the text
        3. TTS → audio URL

        Returns (AgentResponse, audio_url)
        """
        from app.services.voice_service import get_voice_service
        from app.services.session_service import get_session_service

        session_service = get_session_service()
        voice_service = get_voice_service()

        # Get session to determine language for transcription
        session = await session_service.get_session(phone_number)
        language = session.get("language", "en")

        # STT
        transcribed_text = await voice_service.speech_to_text(audio_bytes, language)
        logger.info("voice_transcribed", text_length=len(transcribed_text))

        if not transcribed_text.strip():
            transcribed_text = "I sent a voice message but it could not be transcribed."

        # Process as text query
        agent_response = await self.process_query(
            query=transcribed_text,
            phone_number=phone_number,
            session_id=session_id,
            conversation_history=conversation_history,
            detected_language=language,
        )

        # TTS
        audio_bytes_out = await voice_service.text_to_speech(
            agent_response.response_text,
            agent_response.language,
        )

        # Upload to S3 and get URL
        job_id = uuid.uuid4().hex[:12]
        audio_url = await voice_service.upload_audio_response(audio_bytes_out, job_id)

        return agent_response, audio_url


_orchestrator: AgentCoreOrchestrator | None = None


def get_orchestrator() -> AgentCoreOrchestrator:
    """Return singleton AgentCore orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentCoreOrchestrator()
    return _orchestrator
