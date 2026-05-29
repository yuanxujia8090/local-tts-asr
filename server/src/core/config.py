"""Application configuration from .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    port: int = 8000
    host: str = "127.0.0.1"
    engine_mode: str = "local"  # local | remote
    remote_engine_url: str = "http://localhost:11434"
    tts_model_path: str = ""
    asr_model_path: str = ""
    aligner_model_path: str = ""
    model_source: str = "modelscope"  # modelscope | huggingface
    model_cache_dir: str = ""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
