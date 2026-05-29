"""Engine protocol — strategy pattern for TTS/ASR backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..core.config import settings


@dataclass
class WordTimestamp:
    """Word-level timestamp."""
    text: str
    start_time: float  # seconds
    end_time: float    # seconds


@dataclass
class ASRResult:
    """Complete ASR result with alignment."""
    language: str
    text: str
    duration: float
    words: list[WordTimestamp]


class TTSEngine(ABC):
    """TTS engine interface."""

    @abstractmethod
    def synthesize(self, text: str, voice: str | None = None,
                   emotion: str | None = None, **kwargs) -> bytes:
        """Generate speech audio from text.

        Args:
            text: Input text to synthesize.
            voice: Speaker/voice ID (e.g. 'Vivian', 'zh_female_01').
            emotion: Emotion/style hint (e.g. 'happy', 'calm').

        Returns:
            Raw audio bytes (WAV format, 16kHz mono).
        """
        ...


class ASREngine(ABC):
    """ASR engine interface."""

    @abstractmethod
    def transcribe(self, audio_bytes: bytes, language: str | None = None) -> ASRResult:
        """Transcribe audio to text with word-level timestamps.

        Args:
            audio_bytes: Raw audio data (any format).

        Returns:
            ASRResult with text and word timestamps.
        """
        ...


class EngineFactory:
    """Factory to create engine instances based on configuration."""

    @staticmethod
    def get_tts_engine() -> TTSEngine:
        if settings.engine_mode == "remote":
            from .remote_engine import RemoteTTSEngine
            return RemoteTTSEngine()

        # Local mode — auto-detect backend
        from ..utils.platform import get_backend, check_mlx_available
        backend = get_backend()

        if backend == "mlx" and check_mlx_available():
            from .local_engine import MLXTTSEngine
            return MLXTTSEngine()
        else:
            from .local_engine import PyTorchTTSEngine
            return PyTorchTTSEngine()

    @staticmethod
    def get_asr_engine() -> ASREngine:
        if settings.engine_mode == "remote":
            from .remote_engine import RemoteASREngine
            return RemoteASREngine()

        from ..utils.platform import get_backend, check_mlx_available
        backend = get_backend()

        if backend == "mlx" and check_mlx_available():
            from .local_engine import MLXASREngine
            return MLXASREngine()
        else:
            from .local_engine import PyTorchASREngine
            return PyTorchASREngine()
