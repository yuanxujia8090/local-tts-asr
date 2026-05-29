"""Remote engine — HTTP forwarding to Ollama/vLLM."""

import httpx
from .base import TTSEngine, ASREngine, ASRResult, WordTimestamp
from ..core.config import settings


class RemoteTTSEngine(TTSEngine):
    """Forward TTS requests to a remote OpenAI-compatible API."""

    def synthesize(self, text: str, voice: str | None = None,
                   emotion: str | None = None, **kwargs) -> bytes:

        payload = {
            "model": "qwen3-tts",
            "input": text,
            "response_format": "wav",
        }
        if voice:
            payload["voice"] = voice
        if emotion:
            payload["emotion"] = emotion

        url = f"{settings.remote_engine_url}/v1/audio/speech"
        headers = {"User-Agent": "qwen3-voice-service/0.1.0"}
        with httpx.Client(timeout=60, headers=headers) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.content


class RemoteASREngine(ASREngine):
    """Forward ASR requests to a remote OpenAI-compatible API."""

    def transcribe(self, audio_bytes: bytes, language: str | None = None) -> ASRResult:

        url = f"{settings.remote_engine_url}/v1/audio/transcriptions"
        headers = {"User-Agent": "qwen3-voice-service/0.1.0"}
        with httpx.Client(timeout=60, headers=headers) as client:
            resp = client.post(
                url,
                files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                data={"model": "qwen3-asr", "response_format": "verbose_json"},
            )
            resp.raise_for_status()
            data = resp.json()

        # Parse response into ASRResult
        words = []
        if "segments" in data and data["segments"]:
            for seg in data["segments"]:
                for word_obj in seg.get("words", []):
                    words.append(WordTimestamp(
                        text=word_obj["word"],
                        start_time=word_obj["start"],
                        end_time=word_obj["end"],
                    ))

        return ASRResult(
            language=data.get("language", "unknown"),
            text=data["text"],
            duration=data.get("duration", 0.0),
            words=words,
        )
