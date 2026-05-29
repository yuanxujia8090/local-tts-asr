"""Tests for EngineFactory — verifies engine selection logic."""

from unittest.mock import patch, MagicMock


def _make_mock_settings(engine_mode: str):
    """Create a mock Settings object with the given engine_mode."""
    mock = MagicMock()
    mock.engine_mode = engine_mode
    return mock


def test_get_tts_engine_returns_remote_when_mode_is_remote():
    """EngineFactory should return RemoteTTSEngine when ENGINE_MODE=remote."""
    mock_settings = _make_mock_settings("remote")

    with patch('src.engines.base.settings', mock_settings):
        from src.engines.base import EngineFactory

        engine = EngineFactory.get_tts_engine()
        assert type(engine).__name__ == 'RemoteTTSEngine'


def test_get_asr_engine_returns_remote_when_mode_is_remote():
    """EngineFactory should return RemoteASREngine when ENGINE_MODE=remote."""
    mock_settings = _make_mock_settings("remote")

    with patch('src.engines.base.settings', mock_settings):
        from src.engines.base import EngineFactory

        engine = EngineFactory.get_asr_engine()
        assert type(engine).__name__ == 'RemoteASREngine'


def test_get_tts_engine_returns_local_when_mode_is_local():
    """EngineFactory should return a local engine (not Remote) when ENGINE_MODE=local."""
    mock_settings = _make_mock_settings("local")

    with patch('src.engines.base.settings', mock_settings):
        from src.engines.base import EngineFactory

        engine = EngineFactory.get_tts_engine()
        assert type(engine).__name__ not in ('RemoteTTSEngine',)


def test_get_asr_engine_returns_local_when_mode_is_local():
    """EngineFactory should return a local engine (not Remote) when ENGINE_MODE=local."""
    mock_settings = _make_mock_settings("local")

    with patch('src.engines.base.settings', mock_settings):
        from src.engines.base import EngineFactory

        engine = EngineFactory.get_asr_engine()
        assert type(engine).__name__ not in ('RemoteASREngine',)


def test_tts_engine_returns_bytes():
    """TTS engine synthesize should return bytes."""
    mock_settings = _make_mock_settings("remote")

    with patch('src.engines.base.settings', mock_settings):
        from src.engines.base import EngineFactory

        engine = EngineFactory.get_tts_engine()

        with patch('src.engines.remote_engine.httpx.Client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.content = b"fake audio data"
            mock_resp.raise_for_status = MagicMock()

            mock_ctx = MagicMock()
            mock_ctx.__enter__.return_value.post.return_value = mock_resp
            mock_ctx.__exit__ = MagicMock()
            mock_client.return_value = mock_ctx

            result = engine.synthesize("hello")
            assert isinstance(result, bytes)


def test_asr_engine_returns_result():
    """ASR engine transcribe should return ASRResult with expected attributes."""
    mock_settings = _make_mock_settings("remote")

    with patch('src.engines.base.settings', mock_settings):
        from src.engines.base import EngineFactory

        engine = EngineFactory.get_asr_engine()

        with patch('src.engines.remote_engine.httpx.Client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "text": "hello world",
                "language": "en",
                "duration": 1.5,
                "segments": [
                    {
                        "start": 0.1, "end": 1.0,
                        "words": [
                            {"word": "hello", "start": 0.1, "end": 0.5},
                            {"word": "world", "start": 0.6, "end": 1.0},
                        ],
                    },
                ],
            }
            mock_resp.raise_for_status = MagicMock()

            mock_ctx = MagicMock()
            mock_ctx.__enter__.return_value.post.return_value = mock_resp
            mock_ctx.__exit__ = MagicMock()
            mock_client.return_value = mock_ctx

            result = engine.transcribe(b"fake audio")

            assert hasattr(result, 'text')
            assert hasattr(result, 'language')
            assert hasattr(result, 'duration')
            assert hasattr(result, 'words')
