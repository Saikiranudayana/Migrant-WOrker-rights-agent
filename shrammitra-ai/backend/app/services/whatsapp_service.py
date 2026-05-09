"""
WhatsApp Business API service.

Handles:
- Sending text messages
- Sending audio messages
- Webhook verification
- Message parsing
- Delivery status tracking
"""
from __future__ import annotations

import hashlib
import hmac

import httpx
import structlog

from app.core.config import get_settings
from app.core.security import verify_whatsapp_signature

logger = structlog.get_logger(__name__)
settings = get_settings()


class WhatsAppService:
    """Client for WhatsApp Business Cloud API."""

    def __init__(self) -> None:
        self._base_url = (
            f"{settings.WHATSAPP_API_BASE_URL}/{settings.WHATSAPP_API_VERSION}"
            f"/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        )
        self._headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    async def send_text_message(
        self,
        to: str,
        message: str,
        preview_url: bool = False,
    ) -> dict:
        """Send a text message to a WhatsApp number."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "body": message,
                "preview_url": preview_url,
            },
        }
        return await self._post(payload)

    async def send_audio_message(self, to: str, audio_url: str) -> dict:
        """Send an audio message (MP3/OGG) to a WhatsApp number."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "audio",
            "audio": {"link": audio_url},
        }
        return await self._post(payload)

    async def send_interactive_message(
        self,
        to: str,
        body: str,
        buttons: list[dict],
    ) -> dict:
        """Send an interactive message with quick-reply buttons."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {"buttons": buttons},
            },
        }
        return await self._post(payload)

    async def mark_message_read(self, message_id: str) -> dict:
        """Mark an incoming message as read."""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        return await self._post(payload)

    async def get_media_url(self, media_id: str) -> str:
        """Retrieve the temporary download URL for a media object."""
        url = (
            f"{settings.WHATSAPP_API_BASE_URL}/{settings.WHATSAPP_API_VERSION}"
            f"/{media_id}"
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=self._headers)
            resp.raise_for_status()
            data = resp.json()
            return data["url"]

    async def download_media(self, media_url: str) -> bytes:
        """Download media bytes from a WhatsApp temporary URL."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(media_url, headers=self._headers)
            resp.raise_for_status()
            return resp.content

    async def _post(self, payload: dict) -> dict:
        """POST to WhatsApp messages API with retry logic."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(
                    self._base_url,
                    json=payload,
                    headers=self._headers,
                )
                resp.raise_for_status()
                result = resp.json()
                logger.debug("whatsapp_message_sent", message_id=result.get("messages", [{}])[0].get("id"))
                return result
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "whatsapp_api_error",
                    status_code=exc.response.status_code,
                    response_body=exc.response.text[:500],
                )
                raise


def verify_webhook(verify_token: str) -> bool:
    """Verify the WhatsApp webhook verification token."""
    return hmac.compare_digest(verify_token, settings.WHATSAPP_VERIFY_TOKEN)


_whatsapp_service: WhatsAppService | None = None


def get_whatsapp_service() -> WhatsAppService:
    """Return singleton WhatsApp service instance."""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
