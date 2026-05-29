"""Tests for automatic mode inference from request parameters."""

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
    mock_model.generate_voice_design.return_value = iter([mock_result])

    local_engine._model_cache.clear()

    engine = local_engine.MLXTTSEngine()

    with patch.object(local_engine, '_get_cached_model', return_value=mock_model):
        with patch.object(local_engine, 'get_backend', return_value='mlx'):
            yield engine, mock_model


def test_infer_voice_design_from_instruct(mock_tts_engine):
    """When instruct is provided but mode is not, infer voice_design."""
    engine, mock_model = mock_tts_engine

    engine.synthesize(
        text="Hello world",
        instruct="A cheerful female voice with a slight smile",
        mode=None,
    )

    mock_model.generate_voice_design.assert_called_once()


def test_infer_voice_design_from_empty_mode(mock_tts_engine):
    """When mode is empty string but instruct is provided, infer voice_design."""
    engine, mock_model = mock_tts_engine

    engine.synthesize(
        text="Hello world",
        instruct="A cheerful female voice with a slight smile",
        mode="",
    )

    mock_model.generate_voice_design.assert_called_once()


def test_custom_voice_takes_precedence_over_instruct(mock_tts_engine):
    """When both voice and instruct are provided with no mode, prefer custom_voice."""
    engine, mock_model = mock_tts_engine

    # Clear the voice_design mock and set up custom_voice mock
    mock_model.reset_mock()
    mock_model.generate.return_value = iter([mock_result := MagicMock(audio=[0.0]*1000, sample_rate=24000)])

    engine.synthesize(
        text="Hello world",
        voice="Vivian",
        instruct="A cheerful female voice with a slight smile",
        mode=None,
    )

    mock_model.generate.assert_called_once()


def test_default_mode_is_custom_voice_when_no_instruct_or_voice(mock_tts_engine):
    """When no mode, voice, or instruct provided, default to custom_voice (which requires voice)."""
    engine, _ = mock_tts_engine

    with pytest.raises(ValueError, match="voice is required for custom_voice"):
        engine.synthesize(
            text="Hello world",
            mode=None,
        )
