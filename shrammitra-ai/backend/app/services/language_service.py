"""
Language detection service.

Detects the language of incoming messages using multiple strategies:
1. FastText-style langdetect (primary)
2. Script-based heuristic detection (fallback for short texts)
3. Defaults to English when confidence is low
"""
from __future__ import annotations

import re
import unicodedata

import structlog
from langdetect import DetectorFactory, detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Ensure deterministic language detection
DetectorFactory.seed = 42

# ── Unicode script ranges for heuristic detection ────────────────────────────
SCRIPT_RANGES = {
    "hi": (0x0900, 0x097F),   # Devanagari (Hindi, Marathi, etc.)
    "kn": (0x0C80, 0x0CFF),   # Kannada
    "ta": (0x0B80, 0x0BFF),   # Tamil
    "te": (0x0C00, 0x0C7F),   # Telugu
    "bn": (0x0980, 0x09FF),   # Bengali
    "or": (0x0B00, 0x0B7F),   # Odia (Oriya)
}

# Map langdetect codes to our supported codes
LANGDETECT_MAP = {
    "hi": "hi",
    "kn": "kn",
    "ta": "ta",
    "te": "te",
    "bn": "bn",
    "or": "or",
    "en": "en",
}


def detect_language_by_script(text: str) -> str | None:
    """
    Heuristic: detect language by Unicode script block.

    Particularly reliable for Indian scripts where langdetect
    may struggle with very short messages.
    """
    char_counts: dict[str, int] = {lang: 0 for lang in SCRIPT_RANGES}
    for char in text:
        code_point = ord(char)
        for lang, (start, end) in SCRIPT_RANGES.items():
            if start <= code_point <= end:
                char_counts[lang] += 1
                break

    max_lang = max(char_counts, key=lambda k: char_counts[k])
    max_count = char_counts[max_lang]

    # Require at least 2 characters in a script for confidence
    if max_count >= 2:
        return max_lang
    return None


def detect_language(text: str) -> tuple[str, float]:
    """
    Detect the language of a text string.

    Returns:
        (language_code, confidence) where language_code is one of
        the supported languages, and confidence is 0.0–1.0.
    """
    if not text or not text.strip():
        return settings.DEFAULT_LANGUAGE, 0.0

    clean_text = text.strip()

    # 1. Script-based detection (high confidence for Indian scripts)
    script_lang = detect_language_by_script(clean_text)
    if script_lang:
        logger.debug("language_detected_by_script", language=script_lang)
        return script_lang, 0.95

    # 2. langdetect statistical model
    try:
        detected_langs = detect_langs(clean_text)
        if detected_langs:
            top = detected_langs[0]
            lang_code = LANGDETECT_MAP.get(top.lang, "en")
            if lang_code in settings.SUPPORTED_LANGUAGES:
                logger.debug(
                    "language_detected_by_model",
                    language=lang_code,
                    confidence=top.prob,
                )
                return lang_code, float(top.prob)
    except LangDetectException:
        logger.debug("langdetect_failed", text_length=len(clean_text))

    # 3. Default to English
    logger.debug("language_detection_defaulting_to_english")
    return settings.DEFAULT_LANGUAGE, 0.5


LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "or": "Odia",
}


def get_language_name(code: str) -> str:
    """Return the display name for a language code."""
    return LANGUAGE_NAMES.get(code, "English")
