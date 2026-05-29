"""Pydantic schemas for TTS/ASR API."""

from pydantic import BaseModel, Field
from typing import Optional


class TTSRequest(BaseModel):
    """OpenAI-compatible TTS request with local extensions."""
    model: str = "qwen3-tts"
    input: str = Field(..., description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Speaker/voice ID (custom_voice mode)")
    emotion: Optional[str] = Field(None, description="Emotion/style hint (custom_voice mode)")
    language: Optional[str] = Field("Auto", description="Language code (Auto/Chinese/English...)")
    response_format: Optional[str] = Field("wav", description="Output format: wav/mp3")
    mode: Optional[str] = Field("custom_voice", description="TTS mode: custom_voice, voice_clone, voice_design")
    ref_audio: Optional[str] = Field(None, description="Reference audio path (voice_clone mode)")
    ref_text: Optional[str] = Field(None, description="Reference text (voice_clone mode)")
    instruct: Optional[str] = Field(None, description="Voice description (voice_design mode)")


class ASRRequest(BaseModel):
    """OpenAI-compatible ASR request."""
    model: str = "qwen3-asr"
    file: str  # Will be overridden by multipart form
    response_format: Optional[str] = Field("text", description="text/verbose_json/srt/vtt")


class WordTimestampSchema(BaseModel):
    word: str
    start: float
    end: float


class ASRResponse(BaseModel):
    """ASR response with optional word-level alignment."""
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    words: Optional[list[WordTimestampSchema]] = None


class ModelResponse(BaseModel):
    """OpenAI /models response."""
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: 1700000000)
    owned_by: str = "qwen3-voice-service"
