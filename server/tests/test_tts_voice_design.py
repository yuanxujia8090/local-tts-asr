"""Tests for voice_design mode — mlx_audio uses generator pattern."""

from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "src"))


@pytest.fixture
def mock_tts_engine():
    """Provide a mocked TTS engine that doesn't load real models."""
    from src.engines import local_engine

    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.audio = [0.0] * 1000
    mock_result.sample_rate = 24000
    # MLX generate_voice_design is a generator, not (wavs, sr)
    mock_model.generate_voice_design.return_value = iter([mock_result])

    local_engine._model_cache.clear()

    engine = local_engine.MLXTTSEngine()

    with patch.object(local_engine, '_get_cached_model', return_value=mock_model):
        with patch.object(local_engine, 'get_backend', return_value='mlx'):
            yield engine, mock_model


def test_voice_design_uses_generate_voice_design_as_generator(mock_tts_engine):
    """voice_design mode should use model.generate_voice_design as a generator."""
    engine, mock_model = mock_tts_engine

    engine.synthesize(
        text="今天天气真好",
        instruct="温暖、温柔的年轻女性声音，语速偏慢",
        language="Chinese",
        mode="voice_design",
    )

    mock_model.generate_voice_design.assert_called_once()
    call_kwargs = mock_model.generate_voice_design.call_args[1]
    assert call_kwargs["instruct"] == "温暖、温柔的年轻女性声音，语速偏慢"
    assert call_kwargs["language"] == "chinese"


def test_voice_design_english_language_converted(mock_tts_engine):
    """voice_design mode should convert English language to lowercase for mlx_audio."""
    engine, mock_model = mock_tts_engine

    engine.synthesize(
        text="Hello world",
        instruct="Speak in a warm gentle voice",
        language="English",
        mode="voice_design",
    )

    call_kwargs = mock_model.generate_voice_design.call_args[1]
    assert call_kwargs["language"] == "english"
