"""Tests for TTS API endpoint."""

from unittest.mock import patch, MagicMock


def test_tts_endpoint_returns_wav():
    """POST /v1/audio/speech should return WAV audio bytes."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.tts.EngineFactory') as mock_factory:
        mock_engine = MagicMock()
        mock_engine.synthesize.return_value = b"fake wav data"
        mock_factory.get_tts_engine.return_value = mock_engine

        resp = client.post(
            "/v1/audio/speech",
            json={"input": "hello world", "voice": "Vivian"},
        )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"
        assert resp.content == b"fake wav data"


def test_tts_endpoint_returns_mp3():
    """POST /v1/audio/speech with mp3 format should return audio/mpeg."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.tts.EngineFactory') as mock_factory:
        mock_engine = MagicMock()
        mock_engine.synthesize.return_value = b"fake mp3 data"
        mock_factory.get_tts_engine.return_value = mock_engine

        resp = client.post(
            "/v1/audio/speech",
            json={"input": "hello", "response_format": "mp3"},
        )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/mpeg"


def test_tts_endpoint_passes_language():
    """TTS endpoint should pass language to engine."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.tts.EngineFactory') as mock_factory:
        mock_engine = MagicMock()
        mock_engine.synthesize.return_value = b"audio"
        mock_factory.get_tts_engine.return_value = mock_engine

        client.post(
            "/v1/audio/speech",
            json={"input": "hello", "language": "English"},
        )

        mock_engine.synthesize.assert_called_once()
        call_kwargs = mock_engine.synthesize.call_args[1]
        assert call_kwargs["language"] == "English"


def test_tts_endpoint_passes_mode():
    """TTS endpoint should pass mode to engine."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.tts.EngineFactory') as mock_factory:
        mock_engine = MagicMock()
        mock_engine.synthesize.return_value = b"audio"
        mock_factory.get_tts_engine.return_value = mock_engine

        client.post(
            "/v1/audio/speech",
            json={"input": "hello", "mode": "voice_design"},
        )

        mock_engine.synthesize.assert_called_once()
        call_kwargs = mock_engine.synthesize.call_args[1]
        assert call_kwargs["mode"] == "voice_design"


def test_tts_endpoint_returns_500_on_error():
    """TTS endpoint should return 500 when engine raises."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.tts.EngineFactory') as mock_factory:
        mock_engine = MagicMock()
        mock_engine.synthesize.side_effect = RuntimeError("model not loaded")
        mock_factory.get_tts_engine.return_value = mock_engine

        resp = client.post(
            "/v1/audio/speech",
            json={"input": "hello"},
        )

        assert resp.status_code == 500


def test_tts_endpoint_passes_instruct():
    """TTS endpoint should pass instruct to engine for voice_design mode."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.tts.EngineFactory') as mock_factory:
        mock_engine = MagicMock()
        mock_engine.synthesize.return_value = b"audio"
        mock_factory.get_tts_engine.return_value = mock_engine

        client.post(
            "/v1/audio/speech",
            json={
                "input": "hello",
                "mode": "voice_design",
                "instruct": "温柔的女声，音调偏高",
            },
        )

        mock_engine.synthesize.assert_called_once()
        call_kwargs = mock_engine.synthesize.call_args[1]
        assert call_kwargs["instruct"] == "温柔的女声，音调偏高"
