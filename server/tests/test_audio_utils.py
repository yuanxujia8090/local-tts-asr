"""Tests for audio utility functions."""

import os
import tempfile
from src.utils.audio import normalize_audio, audio_to_bytes


def test_normalize_audio_creates_output():
    # Create a minimal WAV file for testing
    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    # Write minimal WAV header (44 bytes) + silence
    with open(wav_path, "wb") as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(b'\x00\x00\x00\x00')  # file size placeholder
        f.write(b'WAVE')
        # fmt chunk
        f.write(b'fmt ')
        f.write(b'\x10\x00\x00\x00')  # chunk size
        f.write(b'\x01\x00')  # PCM format
        f.write(b'\x01\x00')  # mono
        f.write(b'\x00\x3e\x00\x00')  # 16000 Hz sample rate
        f.write(b'\x00\x3e\x00\x00')  # byte rate
        f.write(b'\x01\x00')  # block align
        f.write(b'\x10\x00')  # bits per sample
        f.write(b'data')
        f.write(b'\x04\x00\x00\x00')  # data size (4 bytes of silence)
        f.write(b'\x00\x00\x00\x00')  # silence

    try:
        result_path = normalize_audio(wav_path)
        assert os.path.exists(result_path)
        assert result_path.endswith(".wav")
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
        # Clean up temp file if created
        result_path and os.path.exists(result_path) and os.remove(result_path)


def test_audio_to_bytes():
    fd, path = tempfile.mkstemp(suffix=".wav")
    try:
        test_data = b"hello audio"
        with open(path, "wb") as f:
            f.write(test_data)

        result = audio_to_bytes(path)
        assert result == test_data
    finally:
        os.close(fd)
        os.remove(path)


def test_save_bytes_to_file():
    from src.utils.audio import save_bytes_to_file

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    os.remove(path)

    try:
        save_bytes_to_file(b"test data", path)
        assert os.path.exists(path)
        with open(path, "rb") as f:
            assert f.read() == b"test data"
    finally:
        os.remove(path)
