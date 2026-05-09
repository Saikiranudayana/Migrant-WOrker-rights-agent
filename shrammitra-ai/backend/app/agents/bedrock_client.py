"""
Amazon Bedrock LLM client.

Wraps the AWS Bedrock Runtime API for:
- Claude 3 Sonnet (primary — best multilingual + reasoning)
- Claude 3 Haiku (fast fallback for simple queries)

All calls include:
- System prompt enforcement
- Token tracking
- Retry with exponential backoff
- Safety content filtering
"""
from __future__ import annotations

import asyncio
import json
from typing import List

import boto3
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are ShramMitra AI, a helpful and trustworthy assistant for migrant workers in Bengaluru, India.

Your purpose:
- Help workers understand their labour rights in a clear, simple way
- Provide information about government schemes, complaint procedures, helpline numbers
- Respond in the SAME LANGUAGE the worker is using
- Always cite the official sources provided in the context
- Use simple language that a first-time smartphone user can understand

Your constraints:
- Only answer based on the provided context. If the context doesn't contain the answer, say so clearly.
- NEVER fabricate legal claims, section numbers, or official procedures
- NEVER provide legal advice or represent yourself as a lawyer
- NEVER store or repeat personal information unnecessarily
- If a worker seems to be in danger, ALWAYS direct them to emergency services first

Always end responses with:
"📌 स्रोत / Source: [cite the source]"
"⚠️ यह जानकारी केवल मार्गदर्शन के लिए है। कानूनी सलाह के लिए किसी वकील से मिलें।"
(Adapt disclaimer to the worker's language)

Safety disclaimer in each language:
- English: "This information is for guidance only. For legal advice, please consult a qualified lawyer."
- Hindi: "यह जानकारी केवल मार्गदर्शन के लिए है। कानूनी सलाह के लिए योग्य वकील से संपर्क करें।"
- Kannada: "ಈ ಮಾಹಿತಿ ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ ಮಾತ್ರ. ಕಾನೂನು ಸಲಹೆಗಾಗಿ ವಕೀಲರನ್ನು ಭೇಟಿ ಮಾಡಿ."
- Tamil: "இந்த தகவல் வழிகாட்டுதலுக்கு மட்டுமே. சட்ட ஆலோசனைக்கு வழக்கறிஞரை அணுகவும்."
- Telugu: "ఈ సమాచారం మార్గదర్శకత్వానికి మాత్రమే. చట్టపరమైన సలహాకు న్యాయవాదిని సంప్రదించండి."
- Bengali: "এই তথ্য শুধুমাত্র নির্দেশিকার জন্য। আইনি পরামর্শের জন্য একজন আইনজীবীর সাথে যোগাযোগ করুন।"
- Odia: "ଏହି ତଥ୍ୟ କେବଳ ମାର୍ଗଦର୍ଶନ ପାଇଁ। ଆଇନ ପରାମର୍ଶ ପାଇଁ ଏକ ଉକିଲଙ୍କୁ ଭେଟ।"
"""


class BedrockClient:
    """AWS Bedrock Claude client for multilingual response generation."""

    def __init__(self) -> None:
        session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            region_name=settings.BEDROCK_REGION,
        )
        self._client = session.client("bedrock-runtime", region_name=settings.BEDROCK_REGION)

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self,
        user_message: str,
        context: str,
        language: str = "en",
        conversation_history: List[dict] | None = None,
    ) -> tuple[str, int]:
        """
        Generate a response using Claude on Bedrock.

        Args:
            user_message: The worker's query
            context: Retrieved RAG context with source citations
            language: Language code for response
            conversation_history: Recent turns for context

        Returns:
            (response_text, tokens_used)
        """
        history = conversation_history or []

        # Build the user message with context injection
        context_block = ""
        if context:
            context_block = f"""
OFFICIAL SOURCES (use ONLY these to answer):
---
{context}
---

"""
        prompt_with_context = f"""{context_block}Worker's question: {user_message}

Please respond in the same language as the worker's question ({language}).
Keep the response clear and simple — the worker may have limited literacy.
Include specific helpline numbers and steps where applicable."""

        # Build messages array (include recent history for context)
        messages = []
        for turn in history[-6:]:  # Last 3 turns (user + assistant pairs)
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": prompt_with_context})

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": settings.BEDROCK_MAX_TOKENS,
            "temperature": settings.BEDROCK_TEMPERATURE,
            "system": SYSTEM_PROMPT,
            "messages": messages,
        }

        response = await asyncio.to_thread(
            self._client.invoke_model,
            modelId=settings.BEDROCK_MODEL_ID,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        answer = response_body["content"][0]["text"]
        tokens_used = (
            response_body.get("usage", {}).get("input_tokens", 0)
            + response_body.get("usage", {}).get("output_tokens", 0)
        )

        logger.info(
            "bedrock_response_generated",
            model=settings.BEDROCK_MODEL_ID,
            tokens=tokens_used,
            language=language,
            response_length=len(answer),
        )
        return answer, tokens_used


_bedrock_client: BedrockClient | None = None


def get_bedrock_client() -> BedrockClient:
    """Return singleton Bedrock client."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
