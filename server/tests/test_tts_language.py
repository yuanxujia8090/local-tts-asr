"""Tests for TTS engine language handling."""

from unittest.mock import MagicMock, patch


def test_mlx_tts_english_with_emotion_passes_instruct():
    """MLX TTS should pass instruct to model.generate for custom_voice mode."""
    from src.engines.local_engine import MLXTTSEngine

    engine = MLXTTSEngine()
    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.audio = [0.0] * 1000
    mock_result.sample_rate = 24000
    mock_model.generate.return_value = [mock_result]

    with patch.object(
        __import__('src.engines.local_engine', fromlist=['_get_cached_model']),
        '_get_cached_model', return_value=mock_model
    ):
        with patch('src.engines.local_engine.get_backend', return_value='mlx'):
            engine.synthesize(
                text="Hello world",
                voice="Ryan",
                emotion="happy",
                language="English",
                mode="custom_voice",
            )

    mock_model.generate.assert_called_once()
    call_kwargs = mock_model.generate.call_args[1]
    assert call_kwargs["lang_code"] == "english"


def test_mlx_tts_english_without_emotion_no_instruct():
    """MLX TTS should not pass instruct when no emotion or instruct is provided."""
    from src.engines.local_engine import MLXTTSEngine

    engine = MLXTTSEngine()
    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.audio = [0.0] * 1000
    mock_result.sample_rate = 24000
    mock_model.generate.return_value = [mock_result]

    with patch.object(
        __import__('src.engines.local_engine', fromlist=['_get_cached_model']),
        '_get_cached_model', return_value=mock_model
    ):
        with patch('src.engines.local_engine.get_backend', return_value='mlx'):
            engine.synthesize(
                text="Hello world",
                voice="Ryan",
                language="English",
                mode="custom_voice",
            )

    mock_model.generate.assert_called_once()
    call_kwargs = mock_model.generate.call_args[1]
    assert "instruct" not in call_kwargs


def test_mlx_tts_chinese_with_emotion_passes_instruct():
    """MLX TTS should pass instruct to model.generate for Chinese text."""
    from src.engines.local_engine import MLXTTSEngine

    engine = MLXTTSEngine()
    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.audio = [0.0] * 1000
    mock_result.sample_rate = 24000
    mock_model.generate.return_value = [mock_result]

    with patch.object(
        __import__('src.engines.local_engine', fromlist=['_get_cached_model']),
        '_get_cached_model', return_value=mock_model
    ):
        with patch('src.engines.local_engine.get_backend', return_value='mlx'):
            engine.synthesize(
                text="你好世界",
                voice="Vivian",
                emotion="开心",
                language="Chinese",
                mode="custom_voice",
            )

    mock_model.generate.assert_called_once()
    call_kwargs = mock_model.generate.call_args[1]
    assert call_kwargs["lang_code"] == "chinese"
    assert call_kwargs["instruct"] == "开心"


def test_mlx_tts_language_auto_defaults_to_auto():
    """MLX TTS with language=Auto should pass lang_code='auto'."""
    from src.engines.local_engine import MLXTTSEngine

    engine = MLXTTSEngine()
    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.audio = [0.0] * 1000
    mock_result.sample_rate = 24000
    mock_model.generate.return_value = [mock_result]

    with patch.object(
        __import__('src.engines.local_engine', fromlist=['_get_cached_model']),
        '_get_cached_model', return_value=mock_model
    ):
        with patch('src.engines.local_engine.get_backend', return_value='mlx'):
            engine.synthesize(
                text="Hello world",
                voice="Ryan",
                mode="custom_voice",
            )

    mock_model.generate.assert_called_once()
    call_kwargs = mock_model.generate.call_args[1]
    assert call_kwargs["lang_code"] == "auto"


def test_mlx_tts_voice_design_passes_instruct():
    """MLX TTS voice_design mode should pass instruct to model.generate_voice_design."""
    from src.engines.local_engine import MLXTTSEngine

    engine = MLXTTSEngine()
    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.audio = [0.0] * 1000
    mock_result.sample_rate = 24000
    # MLX generate_voice_design is a generator, not (wavs, sr)
    mock_model.generate_voice_design.return_value = iter([mock_result])

    with patch.object(
        __import__('src.engines.local_engine', fromlist=['_get_cached_model']),
        '_get_cached_model', return_value=mock_model
    ):
        with patch('src.engines.local_engine.get_backend', return_value='mlx'):
            engine.synthesize(
                text="Hello world",
                language="English",
                mode="voice_design",
                instruct="Speak in a happy tone",
            )

    mock_model.generate_voice_design.assert_called_once()
    call_kwargs = mock_model.generate_voice_design.call_args[1]
    assert call_kwargs["instruct"] == "Speak in a happy tone"
    assert call_kwargs["language"] == "english"


def test_mlx_tts_voice_clone_no_instruct():
    """MLX TTS voice_clone mode should not pass instruct to model.generate."""
    from src.engines.local_engine import MLXTTSEngine

    engine = MLXTTSEngine()
    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.audio = [0.0] * 1000
    mock_result.sample_rate = 24000
    mock_model.generate.return_value = [mock_result]

    with patch.object(
        __import__('src.engines.local_engine', fromlist=['_get_cached_model']),
        '_get_cached_model', return_value=mock_model
    ):
        with patch('src.engines.local_engine.get_backend', return_value='mlx'):
            engine.synthesize(
                text="Hello world",
                language="English",
                mode="voice_clone",
                ref_audio_path="/path/to/ref.wav",
                ref_text="Reference text",
            )

    mock_model.generate.assert_called_once()
    call_kwargs = mock_model.generate.call_args[1]
    assert "instruct" not in call_kwargs
