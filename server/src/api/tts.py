"""TTS API routes — OpenAI compatible /v1/audio/speech."""

import json
import logging
import os
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import Response

from ..engines.base import EngineFactory
from ..schemas.audio import TTSRequest
from ..utils.model_path import ModelNotAvailableError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/speech")
async def synthesize(request: Request):
    """Generate speech from text.

    OpenAI-compatible endpoint with local extensions (voice, emotion).
    Supports three modes: custom_voice, voice_clone, voice_design.
    Returns WAV audio by default.

    Accepts JSON body (application/json) or multipart/form-data.
    For voice_clone mode with file upload, use multipart/form-data with
    ref_audio_file field.
    """
    tmp_path = None
    req: TTSRequest | None = None
    ref_audio_file: UploadFile | None = None

    try:
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            # Parse multipart form data
            form = await request.form()
            req = TTSRequest(
                input=form.get("input", ""),
                voice=form.get("voice"),
                emotion=form.get("emotion"),
                language=form.get("language") or "Auto",
                response_format=form.get("response_format") or "wav",
                mode=form.get("mode") or "custom_voice",
                ref_text=form.get("ref_text"),
                instruct=form.get("instruct"),
                temperature=float(form["temperature"]) if form.get("temperature") else None,
                top_p=float(form["top_p"]) if form.get("top_p") else None,
                max_new_tokens=int(form["max_new_tokens"]) if form.get("max_new_tokens") else None,
            )
            ref_audio_file = form.get("ref_audio_file")  # type: ignore[assignment]
        else:
            # Parse JSON body
            body = await request.json()
            req = TTSRequest(**body)

        # Handle voice_clone file upload — save to temp file for engine
        ref_audio_path = req.ref_audio  # from JSON body (string path)
        if ref_audio_file:
            fd, tmp_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            content = await ref_audio_file.read()
            with open(tmp_path, "wb") as f:
                f.write(content)
            ref_audio_path = tmp_path

        logger.info(f"TTS request: mode={req.mode}, voice={req.voice}, language={req.language}, text_len={len(req.input)}")

        engine = EngineFactory.get_tts_engine()
        logger.info(f"TTS engine: {type(engine).__name__}")

        audio_bytes = engine.synthesize(
            text=req.input,
            voice=req.voice,
            emotion=req.emotion,
            language=req.language or "Auto",
            mode=req.mode or "custom_voice",
            ref_audio_path=ref_audio_path,
            ref_text=req.ref_text,
            instruct=req.instruct,
            temperature=getattr(req, "temperature", None),
            top_p=getattr(req, "top_p", None),
            max_new_tokens=getattr(req, "max_new_tokens", None),
        )
        logger.info(f"TTS success: {len(audio_bytes)} bytes")

    except ModelNotAvailableError as e:
        logger.warning(f"Model not available: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.warning(f"TTS validation error: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid request: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS engine error: {str(e)}")
    finally:
        # Cleanup temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    fmt = req.response_format or "wav"  # type: ignore[union-attr]
    content_type = {"wav": "audio/wav", "mp3": "audio/mpeg"}.get(fmt, "audio/wav")

    return Response(content=audio_bytes, media_type=content_type)  # type: ignore[name-defined]
