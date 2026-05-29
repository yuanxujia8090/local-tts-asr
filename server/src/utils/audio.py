"""Audio processing utilities — FFmpeg normalization."""

import subprocess
import tempfile
import os


def normalize_audio(input_path: str, output_path: str | None = None) -> str:
    """Normalize audio to 16kHz mono PCM WAV.

    Args:
        input_path: Path to input audio file (any format FFmpeg supports).
        output_path: Optional output path. If None, returns temp file.

    Returns:
        Path to normalized WAV file.
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    return output_path


def audio_to_bytes(audio_path: str) -> bytes:
    """Read audio file as bytes."""
    with open(audio_path, "rb") as f:
        return f.read()


def save_bytes_to_file(data: bytes, path: str) -> None:
    """Write bytes to file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
