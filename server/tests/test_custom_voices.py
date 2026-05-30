"""Tests for custom_voices API — security and validation."""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock


def _make_mock_index(voices: list[dict] | None = None) -> str:
    """Create a temp directory with voices.json for testing."""
    tmpdir = tempfile.mkdtemp()
    index_path = os.path.join(tmpdir, "voices.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(voices or [], f)
    return tmpdir


def _save_voice(client, name: str, filename: str, data: bytes):
    """Helper to save a custom voice via TestClient."""
    return client.post(
        "/v1/custom-voices/voices",
        data={"name": name},
        files={"ref_audio": (filename, data)},
    )


def test_save_custom_voice_rejects_path_traversal_in_filename():
    """POST /v1/custom-voices/voices should reject filenames with directory traversal."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "../../../etc/passwd.wav", b"fake audio")

    assert resp.status_code == 422


def test_save_custom_voice_rejects_non_audio_extensions():
    """POST /v1/custom-voices/voices should reject non-audio file extensions."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "script.sh", b"#!/bin/bash")

    assert resp.status_code == 422


def test_save_custom_voice_allows_wav_extension():
    """POST /v1/custom-voices/voices should accept .wav files."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "test.wav", b"RIFF\x00WAVE")

    assert resp.status_code == 200


def test_save_custom_voice_allows_mp3_extension():
    """POST /v1/custom-voices/voices should accept .mp3 files."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "test.mp3", b"fake mp3 data")

    assert resp.status_code == 200


def test_get_custom_voice_audio_blocks_path_traversal():
    """GET /v1/custom-voices/voices/{id}/audio should block path traversal in index."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    tmpdir = _make_mock_index([
        {
            "id": "malicious",
            "name": "evil",
            "filename": "../../../etc/passwd.wav",
            "created_at": "2025-01-01T00:00:00+00:00",
        }
    ])

    with patch("src.api.custom_voices.VOICES_DIR", tmpdir):
        with patch("src.api.custom_voices.VOICES_INDEX", os.path.join(tmpdir, "voices.json")):
            resp = client.get("/v1/custom-voices/voices/malicious/audio")

    assert resp.status_code == 403


def test_delete_custom_voice_blocks_path_traversal():
    """DELETE /v1/custom-voices/voices/{id} should block path traversal in index."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    tmpdir = _make_mock_index([
        {
            "id": "malicious",
            "name": "evil",
            "filename": "../../../etc/cron.d/evil.sh",
            "created_at": "2025-01-01T00:00:00+00:00",
        }
    ])

    with patch("src.api.custom_voices.VOICES_DIR", tmpdir):
        with patch("src.api.custom_voices.VOICES_INDEX", os.path.join(tmpdir, "voices.json")):
            resp = client.delete("/v1/custom-voices/voices/malicious")

    assert resp.status_code == 403


def test_save_custom_voice_allows_flac_extension():
    """POST /v1/custom-voices/voices should accept .flac files."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "test.flac", b"fake flac data")

    assert resp.status_code == 200


def test_save_custom_voice_allows_ogg_extension():
    """POST /v1/custom-voices/voices should accept .ogg files."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "test.ogg", b"fake ogg data")

    assert resp.status_code == 200


def test_save_custom_voice_rejects_exe_extension():
    """POST /v1/custom-voices/voices should reject .exe files."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "malware.exe", b"MZ\x90")

    assert resp.status_code == 422


def test_save_custom_voice_allows_uppercase_wav():
    """POST /v1/custom-voices/voices should accept .WAV (case-insensitive)."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "test.WAV", b"RIFF\x00WAVE")

    assert resp.status_code == 200


def test_save_custom_voice_rejects_no_extension():
    """POST /v1/custom-voices/voices should reject files with no extension."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "noextension", b"some data")

    assert resp.status_code == 422


def test_get_custom_voice_audio_returns_valid_file():
    """GET /v1/custom-voices/voices/{id}/audio should return the audio file."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    save_resp = _save_voice(client, "test_voice", "test.wav", b"RIFF\x00WAVE")
    assert save_resp.status_code == 200
    voice_id = save_resp.json()["id"]

    resp = client.get(f"/v1/custom-voices/voices/{voice_id}/audio")
    assert resp.status_code == 200


def test_get_custom_voice_audio_returns_404_for_unknown_id():
    """GET /v1/custom-voices/voices/{id}/audio should return 404 for unknown ID."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = client.get("/v1/custom-voices/voices/nonexistent/audio")
    assert resp.status_code == 404


def test_load_index_handles_corrupted_json():
    """_load_index should return empty list when JSON is corrupted."""
    from src.api.custom_voices import _load_index

    tmpdir = tempfile.mkdtemp()
    index_path = os.path.join(tmpdir, "voices.json")

    # Write corrupted JSON
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("{corrupted json!!!}")

    with patch("src.api.custom_voices.VOICES_DIR", tmpdir):
        with patch("src.api.custom_voices.VOICES_INDEX", index_path):
            result = _load_index()

    assert result == []


def test_save_custom_voice_rejects_js_extension():
    """POST /v1/custom-voices/voices should reject .js files."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "script.js", b"console.log('xss')")

    assert resp.status_code == 422


def test_save_custom_voice_rejects_html_extension():
    """POST /v1/custom-voices/voices should reject .html files."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = _save_voice(client, "test_voice", "page.html", b"<script>alert(1)</script>")

    assert resp.status_code == 422


def test_delete_custom_voice_allows_valid_id():
    """DELETE /v1/custom-voices/voices/{id} should work for valid IDs."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    save_resp = _save_voice(client, "test_voice", "test.wav", b"RIFF\x00WAVE")
    assert save_resp.status_code == 200
    voice_id = save_resp.json()["id"]

    resp = client.delete(f"/v1/custom-voices/voices/{voice_id}")
    assert resp.status_code == 200


def test_delete_custom_voice_returns_404_for_unknown_id():
    """DELETE /v1/custom-voices/voices/{id} should return 404 for unknown ID."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    resp = client.delete("/v1/custom-voices/voices/nonexistent")
    assert resp.status_code == 404
