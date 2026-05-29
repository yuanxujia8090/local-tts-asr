"""Test remote engine forwarding."""

from unittest.mock import patch, MagicMock


def test_remote_tts_forwards_request():
    """Test that RemoteTTSEngine forwards requests to remote API."""
    from src.engines.remote_engine import RemoteTTSEngine

    engine = RemoteTTSEngine()

    with patch('src.engines.remote_engine.httpx.Client') as mock_client:
        mock_resp = MagicMock()
        mock_resp.content = b"fake audio data"
        mock_resp.raise_for_status = MagicMock()

        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value.post.return_value = mock_resp
        mock_ctx.__exit__ = MagicMock()
        mock_client.return_value = mock_ctx

        result = engine.synthesize("hello world", voice="Vivian")
        assert result == b"fake audio data"


def test_remote_asr_forwards_request():
    """Test that RemoteASREngine forwards requests to remote API."""
    from src.engines.remote_engine import RemoteASREngine

    engine = RemoteASREngine()

    with patch('src.engines.remote_engine.httpx.Client') as mock_client:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "text": "hello world",
            "language": "en",
            "duration": 1.5,
            "segments": [
                {
                    "start": 0.1,
                    "end": 1.0,
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

        result = engine.transcribe(b"fake audio data")
        assert result.text == "hello world"
        assert len(result.words) == 2
