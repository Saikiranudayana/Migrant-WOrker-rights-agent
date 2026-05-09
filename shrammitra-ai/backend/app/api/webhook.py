"""
WhatsApp webhook endpoint.

Handles:
- GET /webhook/whatsapp — webhook verification (Meta challenge)
- POST /webhook/whatsapp — incoming message processing

Security:
- HMAC-SHA256 signature verification on all POST requests
- Idempotency via Redis deduplication
- Async non-blocking processing (WhatsApp requires 200 within 5s)
"""
from __future__ import annotations

import asyncio
import uuid

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import PlainTextResponse

from app.agents.orchestrator import get_orchestrator
from app.core.config import get_settings
from app.core.security import verify_whatsapp_signature
from app.models.schemas import WhatsAppWebhookPayload
from app.services.session_service import get_session_service
from app.services.voice_service import get_voice_service
from app.services.whatsapp_service import get_whatsapp_service, verify_webhook
from app.utils.conversation_logger import log_conversation_message

logger = structlog.get_logger(__name__)
settings = get_settings()
router = APIRouter()


@router.get("/whatsapp", response_class=PlainTextResponse)
async def verify_whatsapp_webhook(
    hub_mode: str | None = None,
    hub_challenge: str | None = None,
    hub_verify_token: str | None = None,
) -> str:
    """
    WhatsApp webhook verification endpoint.

    Meta sends a GET request with hub.challenge when you first
    configure the webhook URL. We must echo back the challenge.
    """
    # Query params use hub.mode etc. — FastAPI maps . to _
    if hub_mode == "subscribe" and hub_verify_token and verify_webhook(hub_verify_token):
        logger.info("whatsapp_webhook_verified")
        return hub_challenge or ""

    logger.warning(
        "webhook_verification_failed",
        mode=hub_mode,
        has_token=bool(hub_verify_token),
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Webhook verification failed.",
    )


@router.post("/whatsapp", status_code=status.HTTP_200_OK)
async def receive_whatsapp_message(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Receive and process incoming WhatsApp messages.

    Returns 200 immediately — actual processing happens in background
    to meet WhatsApp's 5-second response deadline.
    """
    # ── Signature verification ─────────────────────────────────────────────
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_whatsapp_signature(raw_body, signature):
        logger.warning("invalid_whatsapp_signature")
        # Return 200 to prevent Meta from retrying — but don't process
        return {"status": "ignored"}

    # ── Parse payload ──────────────────────────────────────────────────────
    try:
        payload = WhatsAppWebhookPayload.model_validate(await request.json())
    except Exception as exc:
        logger.warning("webhook_parse_error", error=str(exc))
        return {"status": "ignored"}

    # ── Process in background (non-blocking) ───────────────────────────────
    background_tasks.add_task(_process_webhook_payload, payload)
    return {"status": "ok"}


async def _process_webhook_payload(payload: WhatsAppWebhookPayload) -> None:
    """Process a webhook payload in the background."""
    try:
        for entry in payload.entry:
            for change in entry.changes:
                if change.field != "messages":
                    continue
                messages = change.value.messages
                if not messages:
                    continue
                for message in messages:
                    await _handle_message(message)
    except Exception as exc:
        logger.error("webhook_processing_error", error=str(exc), exc_info=True)


async def _handle_message(message) -> None:
    """Handle a single incoming WhatsApp message."""
    wa_service = get_whatsapp_service()
    session_service = get_session_service()
    orchestrator = get_orchestrator()

    phone_number = message.from_
    wa_message_id = message.id

    structlog.contextvars.bind_contextvars(
        phone_hash=phone_number[-4:],  # Only last 4 digits for logging
        wa_message_id=wa_message_id,
    )

    # ── Deduplication ──────────────────────────────────────────────────────
    is_duplicate = await session_service.check_duplicate_message(wa_message_id)
    if is_duplicate:
        logger.info("duplicate_message_skipped")
        return

    # ── Mark message as read ───────────────────────────────────────────────
    try:
        await wa_service.mark_message_read(wa_message_id)
    except Exception as exc:
        logger.warning("mark_read_failed", error=str(exc))

    # ── Get/create session ─────────────────────────────────────────────────
    session = await session_service.get_session(phone_number)
    conversation_history = await session_service.get_history(phone_number)

    # ── Handle message type ────────────────────────────────────────────────
    try:
        if message.type == "text" and message.text:
            user_text = message.text.body
            logger.info("text_message_received", length=len(user_text))

            # Store user message in session history
            await session_service.add_to_history(phone_number, "user", user_text)

            # Process through AgentCore
            agent_response = await orchestrator.process_query(
                query=user_text,
                phone_number=phone_number,
                session_id=session["session_id"],
                conversation_history=conversation_history,
                detected_language=session.get("language"),
            )

            # Update session language
            await session_service.update_session(
                phone_number, {"language": agent_response.language}
            )

            # Store assistant response in session history
            await session_service.add_to_history(
                phone_number, "assistant", agent_response.response_text
            )

            # Send reply
            await wa_service.send_text_message(phone_number, agent_response.response_text)

            # Log to database (background)
            await log_conversation_message(
                phone_number=phone_number,
                user_message=user_text,
                assistant_response=agent_response.response_text,
                language=agent_response.language,
                sources=agent_response.sources,
                confidence=agent_response.confidence,
                tokens_used=agent_response.tokens_used,
                latency_ms=agent_response.latency_ms,
                wa_message_id=wa_message_id,
                is_voice=False,
            )

        elif message.type == "audio" and message.audio:
            logger.info("audio_message_received", media_id=message.audio.id)
            voice_service = get_voice_service()

            # Download audio from WhatsApp
            media_url = await wa_service.get_media_url(message.audio.id)
            audio_bytes = await wa_service.download_media(media_url)

            # Process voice query
            agent_response, audio_url = await orchestrator.process_voice_query(
                audio_bytes=audio_bytes,
                phone_number=phone_number,
                session_id=session["session_id"],
                conversation_history=conversation_history,
            )

            # Send audio response
            await wa_service.send_audio_message(phone_number, audio_url)
            # Also send text response for accessibility
            await wa_service.send_text_message(phone_number, agent_response.response_text)

            await log_conversation_message(
                phone_number=phone_number,
                user_message="[Voice Message]",
                assistant_response=agent_response.response_text,
                language=agent_response.language,
                sources=agent_response.sources,
                confidence=agent_response.confidence,
                tokens_used=agent_response.tokens_used,
                latency_ms=agent_response.latency_ms,
                wa_message_id=wa_message_id,
                is_voice=True,
            )

        else:
            logger.info("unsupported_message_type", type=message.type)
            # Send a helpful response for unsupported types
            session_lang = session.get("language", "en")
            unsupported_responses = {
                "en": "Please send a text or voice message. I can help you understand your labour rights! 🤝",
                "hi": "कृपया टेक्स्ट या वॉइस संदेश भेजें। मैं आपके श्रम अधिकारों में मदद कर सकता हूं! 🤝",
                "kn": "ದಯವಿಟ್ಟು ಪಠ್ಯ ಅಥವಾ ವಾಯ್ಸ್ ಸಂದೇಶ ಕಳುಹಿಸಿ. ನಿಮ್ಮ ಕಾರ್ಮಿಕ ಹಕ್ಕುಗಳ ಬಗ್ಗೆ ಸಹಾಯ ಮಾಡಲು ನಾನು ಇದ್ದೇನೆ! 🤝",
            }
            await wa_service.send_text_message(
                phone_number,
                unsupported_responses.get(session_lang, unsupported_responses["en"]),
            )

    except Exception as exc:
        logger.error("message_handling_error", error=str(exc), exc_info=True)
        # Send a graceful error message in the worker's language
        session_lang = session.get("language", "en")
        error_responses = {
            "en": "Sorry, I'm having a technical issue. Please try again or call 1800-425-1200.",
            "hi": "माफ करें, तकनीकी समस्या है। कृपया पुनः प्रयास करें या 1800-425-1200 पर कॉल करें।",
        }
        try:
            await wa_service.send_text_message(
                phone_number,
                error_responses.get(session_lang, error_responses["en"]),
            )
        except Exception:
            pass  # Don't crash on error sending
