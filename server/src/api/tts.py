"""TTS API routes — OpenAI compatible /v1/audio/speech."""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..engines.base import EngineFactory
from ..schemas.audio import TTSRequest
from ..utils.model_path import ModelNotAvailableError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/speech")
async def synthesize(req: TTSRequest):
    """Generate speech from text.

    OpenAI-compatible endpoint with local extensions (voice, emotion).
    Supports three modes: custom_voice, voice_clone, voice_design.
    Returns WAV audio by default.
    """
    logger.info(f"TTS request: mode={req.mode}, voice={req.voice}, language={req.language}, text_len={len(req.input)}")
    try:
        engine = EngineFactory.get_tts_engine()
        logger.info(f"TTS engine: {type(engine).__name__}")
        audio_bytes = engine.synthesize(
            text=req.input,
            voice=req.voice,
            emotion=req.emotion,
            language=req.language or "Auto",
            mode=req.mode or "custom_voice",
            ref_audio_path=req.ref_audio,
            ref_text=req.ref_text,
            instruct=req.instruct,
        )
        logger.info(f"TTS success: {len(audio_bytes)} bytes")
    except ModelNotAvailableError as e:
        logger.warning(f"Model not available: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.warning(f"TTS validation error: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"TTS error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS engine error: {str(e)}")

    fmt = req.response_format or "wav"
    content_type = {"wav": "audio/wav", "mp3": "audio/mpeg"}.get(fmt, "audio/wav")

    return Response(content=audio_bytes, media_type=content_type)
