"""
Voice service — Speech-to-Text and Text-to-Speech using AWS.

STT: Amazon Transcribe (supports Hindi, Tamil, Telugu, Kannada, Bengali)
TTS: Amazon Polly (supports multiple Indian languages with natural voices)
"""
from __future__ import annotations

import asyncio
import io
import time
import uuid

import boto3
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Map our language codes to AWS Transcribe language codes
TRANSCRIBE_LANGUAGE_MAP = {
    "en": "en-IN",  # English (India)
    "hi": "hi-IN",  # Hindi (India)
    "ta": "ta-IN",  # Tamil (India)
    "te": "te-IN",  # Telugu (India)
    "kn": "kn-IN",  # Kannada (India)
    "bn": "bn-IN",  # Bengali (India)
    "or": "en-IN",  # Odia — fallback to English (Transcribe doesn't support Odia yet)
}

# Map our language codes to Polly voice IDs (natural Indian voices)
POLLY_VOICE_MAP = {
    "en": ("Kajal", "neural"),     # Indian English
    "hi": ("Kajal", "neural"),     # Hindi (Kajal supports Hindi)
    "ta": ("Aditi", "standard"),   # Tamil
    "te": ("Aditi", "standard"),   # Telugu — fallback
    "kn": ("Aditi", "standard"),   # Kannada — fallback
    "bn": ("Aditi", "standard"),   # Bengali — fallback
    "or": ("Aditi", "standard"),   # Odia — fallback
}


class VoiceService:
    """AWS Transcribe + Polly integration for voice support."""

    def __init__(self) -> None:
        if not settings.ENABLE_VOICE:
            logger.info("voice_disabled", reason="ENABLE_VOICE=false — S3/Transcribe/Polly skipped")
            self._transcribe = None
            self._polly = None
            self._s3 = None
            return

        session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            region_name=settings.AWS_REGION,
        )
        self._transcribe = session.client(
            "transcribe", region_name=settings.TRANSCRIBE_REGION
        )
        self._polly = session.client("polly", region_name=settings.POLLY_REGION)
        self._s3 = session.client("s3", region_name=settings.AWS_REGION)

    async def speech_to_text(self, audio_bytes: bytes, language: str = "en") -> str:
        """
        Transcribe audio bytes to text using Amazon Transcribe.
        Returns empty string if voice is disabled (ENABLE_VOICE=false).
        """
        if not settings.ENABLE_VOICE:
            logger.warning("speech_to_text_skipped", reason="ENABLE_VOICE=false")
            return ""

        lang_code = TRANSCRIBE_LANGUAGE_MAP.get(language, "en-IN")
        job_name = f"shrammitra-{uuid.uuid4().hex[:8]}-{int(time.time())}"
        s3_key = f"audio/transcribe/{job_name}.ogg"

        # Upload audio to S3
        await asyncio.to_thread(
            self._s3.put_object,
            Bucket=settings.S3_BUCKET_AUDIO,
            Key=s3_key,
            Body=audio_bytes,
            ContentType="audio/ogg",
        )

        s3_uri = f"s3://{settings.S3_BUCKET_AUDIO}/{s3_key}"

        # Start transcription job
        await asyncio.to_thread(
            self._transcribe.start_transcription_job,
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": s3_uri},
            MediaFormat="ogg",
            LanguageCode=lang_code,
            Settings={"ShowSpeakerLabels": False},
        )

        # Poll for completion (max 60 seconds)
        for _ in range(30):
            await asyncio.sleep(2)
            response = await asyncio.to_thread(
                self._transcribe.get_transcription_job,
                TranscriptionJobName=job_name,
            )
            job_status = response["TranscriptionJob"]["TranscriptionJobStatus"]

            if job_status == "COMPLETED":
                transcript_uri = response["TranscriptionJob"]["Transcript"][
                    "TranscriptFileUri"
                ]
                import httpx
                async with httpx.AsyncClient() as client:
                    result = await client.get(transcript_uri)
                    data = result.json()
                    transcript = data["results"]["transcripts"][0]["transcript"]
                    logger.info("transcription_complete", job_name=job_name)
                    return transcript

            elif job_status == "FAILED":
                failure_reason = response["TranscriptionJob"].get("FailureReason", "unknown")
                logger.error("transcription_failed", reason=failure_reason)
                return ""

        logger.error("transcription_timeout", job_name=job_name)
        return ""

    async def text_to_speech(self, text: str, language: str = "en") -> bytes:
        """
        Convert text to speech using Amazon Polly.
        Returns empty bytes if voice is disabled (ENABLE_VOICE=false).
        """
        if not settings.ENABLE_VOICE:
            logger.warning("text_to_speech_skipped", reason="ENABLE_VOICE=false")
            return b""

        voice_id, engine = POLLY_VOICE_MAP.get(language, ("Aditi", "standard"))

        # Truncate text to Polly's limit (3000 chars for standard, 3000 for neural)
        text = text[:2900]

        response = await asyncio.to_thread(
            self._polly.synthesize_speech,
            Text=text,
            OutputFormat="mp3",
            VoiceId=voice_id,
            Engine=engine,
            LanguageCode=TRANSCRIBE_LANGUAGE_MAP.get(language, "en-IN"),
        )

        audio_stream = response["AudioStream"]
        return audio_stream.read()

    async def upload_audio_response(self, audio_bytes: bytes, job_id: str) -> str:
        """
        Upload TTS audio to S3 and return a pre-signed URL.
        Returns empty string if voice is disabled (ENABLE_VOICE=false).
        """
        if not settings.ENABLE_VOICE:
            return ""

        s3_key = f"audio/responses/{job_id}.mp3"
        await asyncio.to_thread(
            self._s3.put_object,
            Bucket=settings.S3_BUCKET_AUDIO,
            Key=s3_key,
            Body=audio_bytes,
            ContentType="audio/mpeg",
        )

        # Generate pre-signed URL (valid 1 hour)
        url = await asyncio.to_thread(
            self._s3.generate_presigned_url,
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_AUDIO, "Key": s3_key},
            ExpiresIn=3600,
        )
        return url


_voice_service: VoiceService | None = None


def get_voice_service() -> VoiceService:
    """Return singleton VoiceService instance."""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
