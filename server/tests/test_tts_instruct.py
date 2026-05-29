"""Tests for TTS engine instruct handling — ensure None instruct is not passed for custom_voice."""

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
    mock_model.generate.return_value = [mock_result]

    local_engine._model_cache.clear()

    engine = local_engine.MLXTTSEngine()

    with patch.object(local_engine, '_get_cached_model', return_value=mock_model):
        with patch.object(local_engine, 'get_backend', return_value='mlx'):
            yield engine, mock_model


def test_custom_voice_with_none_instruct_does_not_pass_instruct(mock_tts_engine):
    """When instruct is None for custom_voice, model.generate should not receive instruct param.

    This prevents the model from producing silence when no meaningful instruction is provided.
    The Qwen3-TTS CustomVoice model may fail to generate audio for non-Chinese text when
    instruct is set to empty or meaningless values.
    """
    engine, mock_model = mock_tts_engine

    engine.synthesize(
        text="Hello world",
        voice="Ryan",
        language="English",
        mode="custom_voice",
    )

    mock_model.generate.assert_called_once()
    call_kwargs = mock_model.generate.call_args[1]
    # instruct should NOT be passed when it's None
    assert "instruct" not in call_kwargs


def test_custom_voice_with_empty_string_instruct_does_not_pass_instruct(mock_tts_engine):
    """When instruct is empty string for custom_voice, model.generate should not receive instruct param."""
    engine, mock_model = mock_tts_engine

    engine.synthesize(
        text="Hello world",
        voice="Ryan",
        instruct="",
        language="English",
        mode="custom_voice",
    )

    mock_model.generate.assert_called_once()
    call_kwargs = mock_model.generate.call_args[1]
    assert "instruct" not in call_kwargs


def test_custom_voice_with_valid_instruct_passes_instruct(mock_tts_engine):
    """When instruct has meaningful content, it should be passed to model.generate."""
    engine, mock_model = mock_tts_engine

    engine.synthesize(
        text="Hello world",
        voice="Ryan",
        instruct="Speak in a cheerful tone",
        language="English",
        mode="custom_voice",
    )

    mock_model.generate.assert_called_once()
    call_kwargs = mock_model.generate.call_args[1]
    assert call_kwargs["instruct"] == "Speak in a cheerful tone"


def test_custom_voice_with_emotion_as_instruct(mock_tts_engine):
    """When only emotion is provided (no instruct), emotion becomes instruct.

    For custom_voice mode, single-word emotions like 'happy' should still be passed
    as instruct since that's the user's explicit intent.
    """
    engine, mock_model = mock_tts_engine

    engine.synthesize(
        text="Hello world",
        voice="Ryan",
        emotion="happy",
        language="English",
        mode="custom_voice",
    )

    mock_model.generate.assert_called_once()
    call_kwargs = mock_model.generate.call_args[1]
    assert call_kwargs["instruct"] == "happy"
