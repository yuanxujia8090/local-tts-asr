"""Model path resolution — download from ModelScope or HuggingFace."""

import os


class ModelNotAvailableError(Exception):
    """Raised when model is not available locally and auto-download is disabled."""


MODEL_DOWNLOAD_URLS = {
    "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-4bit": "https://modelscope.cn/mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-4bit",
    "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit": "https://modelscope.cn/mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit",
    "mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit": "https://modelscope.cn/mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit",
    "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit": "https://modelscope.cn/mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit",
    "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit": "https://modelscope.cn/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit",
    "mlx-community/Qwen3-ASR-1.7B-8bit": "https://modelscope.cn/mlx-community/Qwen3-ASR-1.7B-8bit",
    "mlx-community/Qwen3-ASR-0.6B-8bit": "https://modelscope.cn/mlx-community/Qwen3-ASR-0.6B-8bit",
    "mlx-community/Qwen3-ForcedAligner-0.6B-8bit": "https://modelscope.cn/mlx-community/Qwen3-ForcedAligner-0.6B-8bit",
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice": "https://modelscope.cn/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice": "https://modelscope.cn/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign": "https://modelscope.cn/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base": "https://modelscope.cn/Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base": "https://modelscope.cn/Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "Qwen/Qwen3-ASR-1.7B": "https://modelscope.cn/Qwen/Qwen3-ASR-1.7B",
    "Qwen/Qwen3-ASR-0.6B": "https://modelscope.cn/Qwen/Qwen3-ASR-0.6B",
    "Qwen/Qwen3-ForcedAligner-0.6B": "https://modelscope.cn/Qwen/Qwen3-ForcedAligner-0.6B",
}


def get_model_source() -> str:
    from ..core.config import settings
    return settings.model_source


def get_model_cache_dir() -> str:
    from ..core.config import settings
    return settings.model_cache_dir


def _ensure_env(cache_dir: str):
    if cache_dir:
        os.environ["MODELSCOPE_CACHE"] = cache_dir
        os.environ["HF_HOME"] = cache_dir


def resolve_model_path(model_id: str) -> str:
    """Resolve model ID to local path.

    1. If model_id is existing directory → use directly
    2. Check LMStudio models directory
    3. Else raise ModelNotAvailableError with download instructions
    """
    if os.path.isdir(model_id):
        return model_id

    # Check LMStudio models directory
    lmstudio_dir = os.path.expanduser("~/.lmstudio/models")
    candidate = os.path.join(lmstudio_dir, model_id)
    if os.path.isdir(candidate):
        print(f"[ModelPath] Found local model: {candidate}")
        return candidate

    # No auto-download — raise error with download link
    url = MODEL_DOWNLOAD_URLS.get(model_id, "https://modelscope.cn")
    raise ModelNotAvailableError(
        f"Model not found locally: {model_id}\n\n"
        f"Please download and place it in ~/.lmstudio/models/:\n"
        f"  ModelScope: {url}\n"
        f"\n"
        f"Or set TTS_MODEL_PATH / ASR_MODEL_PATH in .env to a local model directory."
    )


def _resolve_modelscope(model_id: str) -> str:
    try:
        from modelscope.hub.snapshot_download import snapshot_download
    except ImportError:
        raise ImportError("modelscope not installed. Run: uv sync")

    print(f"[ModelScope] Checking model: {model_id}...")
    local_path = snapshot_download(model_id, cache_dir=None)
    print(f"  -> Found at: {local_path}")
    return local_path


def _resolve_huggingface(model_id: str) -> str:
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise ImportError("huggingface_hub not installed. Run: uv sync")

    print(f"[HuggingFace] Checking model: {model_id}...")
    local_path = snapshot_download(model_id, cache_dir=None)
    print(f"  -> Found at: {local_path}")
    return local_path
