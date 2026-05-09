"""Integration tests for the WhatsApp webhook endpoints."""
import hashlib
import hmac
import json
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


def make_signature(payload: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode(), payload, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


WEBHOOK_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "test_entry_id",
            "changes": [
                {
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "911234567890",
                            "phone_number_id": "test_phone_id",
                        },
                        "messages": [
                            {
                                "from": "919876543210",
                                "id": "wamid.test123",
                                "timestamp": "1700000000",
                                "type": "text",
                                "text": {"body": "What is minimum wage?"},
                            }
                        ],
                    },
                    "field": "messages",
                }
            ],
        }
    ],
}


class TestWebhookVerification:
    async def test_valid_verify_token(self, client):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.WHATSAPP_VERIFY_TOKEN = "test_verify_token"
            response = await client.get(
                "/webhook/whatsapp",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "test_verify_token",
                    "hub.challenge": "challenge_abc123",
                },
            )
        assert response.status_code == 200
        assert response.text == "challenge_abc123"

    async def test_invalid_verify_token_rejected(self, client):
        response = await client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "challenge_abc123",
            },
        )
        assert response.status_code == 403


class TestWebhookIncoming:
    async def test_valid_signature_returns_200(self, client):
        payload = json.dumps(WEBHOOK_PAYLOAD).encode()
        secret = "test_app_secret"
        signature = make_signature(payload, secret)

        with patch("app.core.config.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.WHATSAPP_APP_SECRET = secret
            settings.is_production = False

            with patch("app.api.webhook._process_webhook_payload", new_callable=AsyncMock):
                response = await client.post(
                    "/webhook/whatsapp",
                    content=payload,
                    headers={
                        "X-Hub-Signature-256": signature,
                        "Content-Type": "application/json",
                    },
                )
        assert response.status_code == 200

    async def test_invalid_signature_returns_403(self, client):
        payload = json.dumps(WEBHOOK_PAYLOAD).encode()
        response = await client.post(
            "/webhook/whatsapp",
            content=payload,
            headers={
                "X-Hub-Signature-256": "sha256=invalid",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 403
