"""Platform detection — auto-detect compute backend."""

import os
import platform


def is_macos() -> bool:
    return platform.system() == "Darwin"


def get_backend() -> str:
    """Get compute backend. Priority: ENGINE_MODE env > auto-detect."""
    mode = os.environ.get("ENGINE_MODE", "").lower()
    if mode in ("local", "remote"):
        return mode

    return "mlx" if is_macos() else "cuda"


def get_backend_label() -> str:
    backend = get_backend()
    labels = {"mlx": "mlx (Apple Silicon)", "cuda": "cuda (NVIDIA GPU)", "remote": "remote"}
    return labels.get(backend, backend)


def check_mlx_available() -> bool:
    try:
        import mlx_audio  # noqa: F401
        return True
    except ImportError:
        return False


def check_torch_available() -> bool:
    try:
        import torch  # noqa: F401
        return True
    except ImportError:
        return False
