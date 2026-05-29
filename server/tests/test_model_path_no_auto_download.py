"""Tests for model auto-download prevention."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent / "src"))


class TestResolveModelPathNoAutoDownload:
    """resolve_model_path should NOT auto-download when model is not found locally."""

    def test_raises_when_model_not_local(self):
        """When model is not in local dirs, should raise ModelNotAvailable (not download)."""
        from src.utils.model_path import resolve_model_path

        with patch('src.utils.model_path.os.path.isdir', return_value=False):
            with pytest.raises(Exception) as exc_info:
                resolve_model_path("mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-4bit")

        err = str(exc_info.value).lower()
        assert "download" in err or "not found" in err

    def test_returns_path_when_model_exists_locally(self):
        """When model_id is an existing directory, should return path directly."""
        from src.utils.model_path import resolve_model_path

        with patch('src.utils.model_path.os.path.isdir', return_value=True):
            result = resolve_model_path("/some/local/model/path")

        assert result == "/some/local/model/path"

    def test_returns_lmstudio_path_when_model_exists(self):
        """When model exists in ~/.lmstudio/models/<model_id>, should return it."""
        from src.utils.model_path import resolve_model_path

        def mock_isdir(path):
            if path == "/Users/test/.lmstudio/models/some/model_id":
                return True
            return False

        with patch('src.utils.model_path.os.path.isdir', side_effect=mock_isdir):
            with patch('os.path.expanduser', return_value='/Users/test/.lmstudio/models'):
                result = resolve_model_path("some/model_id")

        assert "lmstudio" in result
        assert "some/model_id" in result
