"""Tests for language detection service."""
import pytest
from app.services.language_service import detect_language, detect_language_by_script


class TestScriptDetection:
    def test_devanagari_hindi(self):
        lang = detect_language_by_script("मेरा वेतन नहीं मिला")
        assert lang == "hi"

    def test_kannada(self):
        lang = detect_language_by_script("ನನ್ನ ವೇತನ ಸಿಗಲಿಲ್ಲ")
        assert lang == "kn"

    def test_tamil(self):
        lang = detect_language_by_script("என் சம்பளம் கிடைக்கவில்லை")
        assert lang == "ta"

    def test_telugu(self):
        lang = detect_language_by_script("నా జీతం రాలేదు")
        assert lang == "te"

    def test_bengali(self):
        lang = detect_language_by_script("আমার মজুরি পাইনি")
        assert lang == "bn"

    def test_english_returns_none(self):
        lang = detect_language_by_script("My salary was not paid")
        assert lang is None


class TestDetectLanguage:
    def test_hindi_text(self):
        result = detect_language("मुझे काम पर चोट लगी है")
        assert result.language == "hi"
        assert result.confidence >= 0.9

    def test_english_text(self):
        result = detect_language("What are my rights as a worker?")
        assert result.language == "en"

    def test_empty_returns_english(self):
        result = detect_language("")
        assert result.language == "en"
        assert result.confidence == 0.5
