"""Custom voice management — save, list, delete, and retrieve saved voices."""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse

router = APIRouter()
logger = logging.getLogger(__name__)

VOICES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "custom_voices")
VOICES_INDEX = os.path.join(VOICES_DIR, "voices.json")

# Only allow safe audio file extensions (case-insensitive)
ALLOWED_AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg"}


def _ensure_dir():
    """Ensure the custom voices directory exists."""
    os.makedirs(VOICES_DIR, exist_ok=True)


def _load_index() -> list[dict]:
    """Load the voices index from disk."""
    _ensure_dir()
    if not os.path.exists(VOICES_INDEX):
        return []
    try:
        with open(VOICES_INDEX, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        logger.warning("Failed to load voices index, returning empty")
        return []


def _save_index(index: list[dict]):
    """Save the voices index to disk."""
    _ensure_dir()
    with open(VOICES_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


@router.get("/voices")
def list_custom_voices():
    """List all saved custom voices."""
    index = _load_index()
    return [
        {
            "id": v["id"],
            "name": v["name"],
            "filename": v["filename"],
            "created_at": v["created_at"],
        }
        for v in index
    ]


@router.post("/voices")
def save_custom_voice(
    name: str = Form(..., description="Name for this custom voice"),
    ref_audio: UploadFile = File(..., description="Reference audio file"),
):
    """Save a reference audio as a custom voice for future use."""
    if not name or not name.strip():
        raise HTTPException(status_code=422, detail="Voice name is required")

    # Read audio content
    content = ref_audio.file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Audio file is empty")

    # Validate filename: no path separators, only safe extension
    if ref_audio.filename and ("/" in ref_audio.filename or "\\" in ref_audio.filename):
        raise HTTPException(
            status_code=422,
            detail="文件名包含非法字符",
        )

    # Validate file extension (case-insensitive)
    ext = os.path.splitext(ref_audio.filename)[1].lower() if ref_audio.filename else ""
    if ext not in ALLOWED_AUDIO_EXTS:
        raise HTTPException(
            status_code=422,
            detail=f"不支持的音频格式: {ref_audio.filename}. 支持的格式: {', '.join(sorted(ALLOWED_AUDIO_EXTS))}",
        )

    # Generate unique ID and save file
    voice_id = f"custom_{uuid.uuid4().hex[:8]}"
    filename = f"{voice_id}{ext}"
    filepath = os.path.join(VOICES_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    # Update index
    index = _load_index()
    entry = {
        "id": voice_id,
        "name": name.strip(),
        "filename": filename,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    index.append(entry)
    _save_index(index)

    logger.info(f"Custom voice saved: {voice_id} ({name.strip()})")
    return entry


@router.delete("/voices/{voice_id}")
def delete_custom_voice(voice_id: str):
    """Delete a saved custom voice."""
    index = _load_index()
    found = None
    for v in index:
        if v["id"] == voice_id:
            found = v
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Custom voice '{voice_id}' not found")

    # Security: prevent path traversal attacks
    filepath = os.path.join(VOICES_DIR, found["filename"])
    real_path = os.path.realpath(filepath)
    if not real_path.startswith(os.path.realpath(VOICES_DIR)):
        raise HTTPException(status_code=403, detail="Invalid file path")

    if os.path.exists(filepath):
        os.remove(filepath)

    # Update index
    _save_index([v for v in index if v["id"] != voice_id])
    logger.info(f"Custom voice deleted: {voice_id}")
    return {"status": "ok", "id": voice_id}


@router.get("/voices/{voice_id}/audio")
def get_custom_voice_audio(voice_id: str):
    """Get the reference audio for a saved custom voice."""
    index = _load_index()
    found = None
    for v in index:
        if v["id"] == voice_id:
            found = v
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Custom voice '{voice_id}' not found")

    # Security: prevent path traversal attacks
    filepath = os.path.join(VOICES_DIR, found["filename"])
    real_path = os.path.realpath(filepath)
    if not real_path.startswith(os.path.realpath(VOICES_DIR)):
        raise HTTPException(status_code=403, detail="Invalid file path")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Audio file not found: {found['filename']}")

    return FileResponse(
        filepath,
        media_type="audio/wav",
        filename=found["filename"],
    )
