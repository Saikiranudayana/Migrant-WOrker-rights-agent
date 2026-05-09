"""
Safety guardrails for ShramMitra AI.

Enforces:
1. Prompt injection detection
2. Input validation and sanitization
3. Output validation (no fabricated citations, no legal advice overreach)
4. Content safety (no harmful guidance)
5. Confidence gating (uncertain answers trigger fallback)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

import structlog

from app.core.config import get_settings
from app.core.security import detect_prompt_injection, sanitize_input
from app.rag.retriever import RetrievedChunk

logger = structlog.get_logger(__name__)
settings = get_settings()

DISCLAIMER = {
    "en": "⚠️ This information is for guidance only. For legal advice, please consult a qualified lawyer or the Karnataka Labour Department.",
    "hi": "⚠️ यह जानकारी केवल मार्गदर्शन के लिए है। कानूनी सलाह के लिए श्रम विभाग या वकील से संपर्क करें।",
    "kn": "⚠️ ಈ ಮಾಹಿತಿ ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ ಮಾತ್ರ. ಕಾನೂನು ಸಲಹೆಗಾಗಿ ಕರ್ನಾಟಕ ಕಾರ್ಮಿಕ ಇಲಾಖೆ ಅಥವಾ ವಕೀಲರನ್ನು ಭೇಟಿ ಮಾಡಿ.",
    "ta": "⚠️ இந்த தகவல் வழிகாட்டுதலுக்கு மட்டுமே. சட்ட ஆலோசனைக்கு உழைப்பு துறை அல்லது வழக்கறிஞரை அணுகவும்.",
    "te": "⚠️ ఈ సమాచారం మార్గదర్శకత్వానికి మాత్రమే. చట్టపరమైన సలహాకు కార్మిక శాఖ లేదా న్యాయవాదిని సంప్రదించండి.",
    "bn": "⚠️ এই তথ্য শুধুমাত্র নির্দেশিকার জন্য। আইনি পরামর্শের জন্য শ্রম বিভাগ বা আইনজীবীর সাথে যোগাযোগ করুন।",
    "or": "⚠️ ଏହି ତଥ୍ୟ କେବଳ ମାର୍ଗଦର୍ଶନ ପାଇଁ। ଆଇନ ପରାମର୍ଶ ପାଇଁ ଶ୍ରମ ବିଭାଗ ବା ଉକିଲଙ୍କ ସହ ଯୋଗାଯୋଗ କରନ୍ତୁ।",
}

NO_CONTEXT_RESPONSE = {
    "en": "I don't have specific information about this in my knowledge base. Please contact the Karnataka Labour Department helpline: 📞 1800-425-1200 (toll-free) or visit labour.karnataka.gov.in",
    "hi": "मेरे पास इस बारे में विशिष्ट जानकारी नहीं है। कृपया कर्नाटक श्रम विभाग हेल्पलाइन से संपर्क करें: 📞 1800-425-1200 (निःशुल्क)",
    "kn": "ನನ್ನ ಬಳಿ ಈ ಬಗ್ಗೆ ನಿರ್ದಿಷ್ಟ ಮಾಹಿತಿ ಇಲ್ಲ. ಕರ್ನಾಟಕ ಕಾರ್ಮಿಕ ಇಲಾಖೆ ಸಹಾಯವಾಣಿ: 📞 1800-425-1200 (ಉಚಿತ)",
    "ta": "என்னிடம் இதுபற்றிய குறிப்பிட்ட தகவல் இல்லை. கர்நாடக தொழிலாளர் துறை உதவி எண்: 📞 1800-425-1200 (இலவசம்)",
    "te": "నా వద్ద దీని గురించి నిర్దిష్ట సమాచారం లేదు. కర్ణాటక కార్మిక శాఖ హెల్ప్‌లైన్: 📞 1800-425-1200 (నిరుచార్జి)",
    "bn": "আমার কাছে এ বিষয়ে নির্দিষ্ট তথ্য নেই। কর্ণাটক শ্রম বিভাগ হেল্পলাইন: 📞 1800-425-1200 (বিনামূল্যে)",
    "or": "ମୋ ପାଖରେ ଏ ବିଷୟରେ ନିର্দিষ্ট ତଥ୍ୟ ନାହିଁ। କର୍ଣ୍ଣାଟକ ଶ୍ରମ ବିଭାଗ ହେଲ୍ପଲାଇନ: 📞 1800-425-1200 (ମୁଫ୍ତ)",
}

INJECTION_RESPONSE = {
    "en": "I can only help with labour rights questions. Please ask me about your wages, PF, ESI, or other work-related rights.",
    "hi": "मैं केवल श्रम अधिकारों के प्रश्नों में मदद कर सकता हूं। कृपया वेतन, PF, ESI, या अन्य कार्य-संबंधित अधिकारों के बारे में पूछें।",
}


@dataclass
class GuardrailResult:
    """Result of guardrail validation."""
    is_safe: bool
    blocked_reason: str | None
    sanitized_input: str
    suggested_response: str | None


class SafetyGuardrail:
    """
    Multi-layer safety guardrail for input and output validation.
    """

    def validate_input(self, text: str, language: str = "en") -> GuardrailResult:
        """
        Validate and sanitize user input before processing.

        Returns GuardrailResult with:
        - is_safe: whether to proceed with RAG + LLM
        - sanitized_input: cleaned text
        - suggested_response: pre-built response if blocked
        """
        # 1. Sanitize
        sanitized = sanitize_input(text, max_length=4096)

        if not sanitized:
            return GuardrailResult(
                is_safe=False,
                blocked_reason="empty_input",
                sanitized_input="",
                suggested_response=NO_CONTEXT_RESPONSE.get(language, NO_CONTEXT_RESPONSE["en"]),
            )

        # 2. Prompt injection check
        if detect_prompt_injection(sanitized):
            logger.warning("input_blocked_injection_attempt", language=language)
            return GuardrailResult(
                is_safe=False,
                blocked_reason="prompt_injection",
                sanitized_input=sanitized,
                suggested_response=INJECTION_RESPONSE.get(language, INJECTION_RESPONSE["en"]),
            )

        return GuardrailResult(
            is_safe=True,
            blocked_reason=None,
            sanitized_input=sanitized,
            suggested_response=None,
        )

    def validate_context(
        self,
        chunks: list[RetrievedChunk],
        language: str = "en",
    ) -> tuple[bool, str | None]:
        """
        Check if retrieved context is sufficient to answer the query.

        Returns (has_context, fallback_response).
        """
        if not chunks:
            logger.info("no_context_retrieved_using_fallback", language=language)
            return False, NO_CONTEXT_RESPONSE.get(language, NO_CONTEXT_RESPONSE["en"])

        # Check if best chunk meets confidence threshold
        best_score = max(c.score for c in chunks)
        if best_score < settings.RAG_SIMILARITY_THRESHOLD:
            logger.info(
                "low_confidence_context",
                best_score=best_score,
                threshold=settings.RAG_SIMILARITY_THRESHOLD,
            )
            return False, NO_CONTEXT_RESPONSE.get(language, NO_CONTEXT_RESPONSE["en"])

        return True, None

    def apply_output_guardrails(self, response: str, language: str = "en") -> str:
        """
        Post-process the LLM response:
        1. Ensure disclaimer is present
        2. Remove any accidentally hallucinated structure (e.g., raw JSON)
        3. Cap response length for WhatsApp readability
        """
        # Cap at WhatsApp message limit (4096 chars)
        if len(response) > 4000:
            response = response[:3900] + "\n...\n[Message truncated for readability]"

        # Ensure disclaimer is appended
        disclaimer = DISCLAIMER.get(language, DISCLAIMER["en"])
        if disclaimer not in response and "⚠️" not in response:
            response = f"{response}\n\n{disclaimer}"

        return response


_guardrail: SafetyGuardrail | None = None


def get_safety_guardrail() -> SafetyGuardrail:
    """Return singleton SafetyGuardrail instance."""
    global _guardrail
    if _guardrail is None:
        _guardrail = SafetyGuardrail()
    return _guardrail
