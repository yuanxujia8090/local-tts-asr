"""Tests for voice_design mode error handling."""

from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_voice_design_without_instruct_returns_422():
    """voice_design mode without instruct should return 422 with clear error."""
    from src.main import app

    client = TestClient(app)
    response = client.post("/v1/audio/speech", json={
        "input": "你好，世界！",
        "mode": "voice_design",
    })

    assert response.status_code == 422


def test_voice_design_with_instruct_succeeds():
    """voice_design mode with instruct should succeed."""
    from src.main import app

    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.audio = [0.0] * 1000
    mock_result.sample_rate = 24000
    mock_model.generate_voice_design.return_value = iter([mock_result])

    with patch("src.engines.local_engine._get_cached_model", return_value=mock_model):
        with patch("src.engines.local_engine.get_backend", return_value="mlx"):
            client = TestClient(app)
            response = client.post("/v1/audio/speech", json={
                "input": "Hello world",
                "mode": "voice_design",
                "instruct": "A cheerful female voice with a slight smile",
            })

    assert response.status_code == 200


def test_voice_design_with_empty_instruct_returns_422():
    """voice_design mode with empty instruct should return 422."""
    from src.main import app

    client = TestClient(app)
    response = client.post("/v1/audio/speech", json={
        "input": "Hello world",
        "mode": "voice_design",
        "instruct": "",
    })

    assert response.status_code == 422


def test_voice_design_infer_from_instruct_without_mode():
    """When mode is omitted but instruct is provided, infer voice_design."""
    from src.main import app

    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.audio = [0.0] * 1000
    mock_result.sample_rate = 24000
    mock_model.generate_voice_design.return_value = iter([mock_result])

    with patch("src.engines.local_engine._get_cached_model", return_value=mock_model):
        with patch("src.engines.local_engine.get_backend", return_value="mlx"):
            client = TestClient(app)
            response = client.post("/v1/audio/speech", json={
                "input": "Hello world",
                "instruct": "A cheerful female voice with a slight smile",
            })

    assert response.status_code == 200
