"""Tests for ASR API endpoint."""

import json
import os
from unittest.mock import patch, MagicMock


def _make_mock_asr_result(text="hello world", language="en", duration=1.5, words=None):
    """Create a mock ASRResult for testing."""
    result = MagicMock()
    result.text = text
    result.language = language
    result.duration = duration
    result.words = words or []
    return result


def _mock_normalize_audio(input_path: str, output_path: str | None = None) -> str:
    """Mock normalize_audio that creates a real temp file."""
    if output_path is None:
        import tempfile
        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

    # Write a minimal valid WAV file so the engine can read it
    with open(output_path, "wb") as f:
        # Minimal WAV header + 4 bytes silence
        f.write(b'RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x00\x3e\x00\x00\x00\x3e\x00\x00\x01\x00\x10\x00data\x04\x00\x00\x00\x00\x00\x00\x00')

    return output_path


def test_asr_endpoint_returns_text():
    """POST /v1/audio/transcriptions with text format should return plain text."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.asr.EngineFactory') as mock_factory:
        mock_engine = MagicMock()
        mock_engine.transcribe.return_value = _make_mock_asr_result("你好世界", "Chinese")
        mock_factory.get_asr_engine.return_value = mock_engine

        with patch('src.api.asr.normalize_audio', side_effect=_mock_normalize_audio):
            resp = client.post(
                "/v1/audio/transcriptions",
                files={"file": ("test.wav", b"fake audio")},
                data={"response_format": "text"},
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/plain; charset=utf-8"
        assert resp.text == "你好世界"


def test_asr_endpoint_returns_json():
    """POST /v1/audio/transcriptions with json format should return JSON."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.asr.EngineFactory') as mock_factory:
        mock_engine = MagicMock()
        mock_engine.transcribe.return_value = _make_mock_asr_result("hello world", "en")
        mock_factory.get_asr_engine.return_value = mock_engine

        with patch('src.api.asr.normalize_audio', side_effect=_mock_normalize_audio):
            resp = client.post(
                "/v1/audio/transcriptions",
                files={"file": ("test.wav", b"fake audio")},
                params={"response_format": "json"},
            )

        assert resp.status_code == 200
        data = json.loads(resp.text)
        assert data["text"] == "hello world"


def test_asr_endpoint_returns_verbose_json():
    """POST /v1/audio/transcriptions with verbose_json should include words."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.asr.EngineFactory') as mock_factory:
        from src.engines.base import WordTimestamp

        words = [
            WordTimestamp(text="hello", start_time=0.1, end_time=0.5),
            WordTimestamp(text="world", start_time=0.6, end_time=1.0),
        ]
        mock_engine = MagicMock()
        mock_engine.transcribe.return_value = _make_mock_asr_result("hello world", "en", 1.5, words)
        mock_factory.get_asr_engine.return_value = mock_engine

        with patch('src.api.asr.normalize_audio', side_effect=_mock_normalize_audio):
            resp = client.post(
                "/v1/audio/transcriptions",
                files={"file": ("test.wav", b"fake audio")},
                params={"response_format": "verbose_json"},
            )

        assert resp.status_code == 200
        data = json.loads(resp.text)
        assert data["text"] == "hello world"
        assert data["language"] == "en"
        assert data["duration"] == 1.5
        assert len(data["segments"]) == 2


def test_asr_endpoint_passes_language():
    """ASR endpoint should pass language to engine."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.asr.EngineFactory') as mock_factory:
        mock_engine = MagicMock()
        mock_engine.transcribe.return_value = _make_mock_asr_result("hello", "en")
        mock_factory.get_asr_engine.return_value = mock_engine

        with patch('src.api.asr.normalize_audio', side_effect=_mock_normalize_audio):
            client.post(
                "/v1/audio/transcriptions",
                files={"file": ("test.wav", b"fake audio")},
                params={"response_format": "text", "language": "English"},
            )

        mock_engine.transcribe.assert_called_once()
        call_kwargs = mock_engine.transcribe.call_args[1]
        assert call_kwargs["language"] == "English"


def test_asr_endpoint_returns_500_on_error():
    """ASR endpoint should return 500 when engine raises."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.asr.EngineFactory') as mock_factory:
        mock_engine = MagicMock()
        mock_engine.transcribe.side_effect = RuntimeError("model not loaded")
        mock_factory.get_asr_engine.return_value = mock_engine

        resp = client.post(
            "/v1/audio/transcriptions",
            files={"file": ("test.wav", b"fake audio")},
        )

        assert resp.status_code == 500


def test_alignment_endpoint_returns_words():
    """POST /v1/audio/alignment should return word-level timestamps."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    with patch('src.api.asr.EngineFactory') as mock_factory:
        from src.engines.base import WordTimestamp

        words = [
            WordTimestamp(text="hello", start_time=0.1, end_time=0.5),
            WordTimestamp(text="world", start_time=0.6, end_time=1.0),
        ]
        mock_engine = MagicMock()
        mock_engine.transcribe.return_value = _make_mock_asr_result("hello world", "en", 1.5, words)
        mock_factory.get_asr_engine.return_value = mock_engine

        with patch('src.api.asr.normalize_audio', side_effect=_mock_normalize_audio):
            resp = client.post(
                "/v1/audio/alignment",
                files={"file": ("test.wav", b"fake audio")},
            )

        assert resp.status_code == 200
        data = json.loads(resp.text)
        assert data["text"] == "hello world"
        assert len(data["words"]) == 2
