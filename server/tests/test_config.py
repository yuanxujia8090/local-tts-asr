"""Tests for config and platform modules."""

import os
import tempfile
from src.core.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.port == 8000
    assert s.engine_mode == "local"


def test_settings_from_env():
    # Use environment variables to override defaults
    old_port = os.environ.get("PORT")
    old_mode = os.environ.get("ENGINE_MODE")
    try:
        os.environ["PORT"] = "9999"
        os.environ["ENGINE_MODE"] = "remote"

        # Create a fresh Settings instance to pick up env vars
        from pydantic_settings import SettingsConfigDict
        from pathlib import Path

        class TestSettings(Settings):
            port: int = 8000
            host: str = "127.0.0.1"
            engine_mode: str = "local"
            remote_engine_url: str = "http://localhost:11434"

            model_config = SettingsConfigDict(
                env_file=str(Path(__file__).parent.parent / "src" / ".env"),
                env_file_encoding="utf-8",
                extra="ignore",
            )

        s = TestSettings()
        assert s.port == 9999
        assert s.engine_mode == "remote"
    finally:
        if old_port is not None:
            os.environ["PORT"] = old_port
        else:
            os.environ.pop("PORT", None)
        if old_mode is not None:
            os.environ["ENGINE_MODE"] = old_mode
        else:
            os.environ.pop("ENGINE_MODE", None)


def test_get_backend_label():
    from src.utils.platform import get_backend_label
    label = get_backend_label()
    assert "mlx" in label.lower() or "cuda" in label.lower()


def test_check_deps_available():
    from src.utils.platform import check_mlx_available, check_torch_available
    # These may or may not be installed — just verify they return bool
    assert isinstance(check_mlx_available(), bool)
    assert isinstance(check_torch_available(), bool)
