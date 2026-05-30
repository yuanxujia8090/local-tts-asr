"""ASR API routes — OpenAI compatible."""

import json
import logging
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import Response

from ..engines.base import EngineFactory, ASRResult
from ..utils.audio import normalize_audio
from ..utils.model_path import ModelNotAvailableError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/transcriptions")
async def transcribe(
    file: UploadFile = File(...),
    model: str = "qwen3-asr",
    response_format: str = Query(default="text"),
    language: str | None = Query(default=None),
):
    """Transcribe audio to text. OpenAI-compatible endpoint."""
    tmp_path = None
    normalized = None
    try:
        content = await file.read()
        logger.info(f"ASR request: filename={file.filename}, size={len(content)}, language={language}")

        fd, tmp_path = tempfile.mkstemp()
        os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(content)

        normalized = normalize_audio(tmp_path)
        logger.info(f"Audio normalized: {normalized}")

        engine = EngineFactory.get_asr_engine()
        logger.info(f"ASR engine: {type(engine).__name__}")
        with open(normalized, "rb") as f:
            audio_bytes = f.read()

        result = engine.transcribe(audio_bytes, language=language)
        logger.info(f"ASR success: text='{result.text[:100]}', language={result.language}")

    except ModelNotAvailableError as e:
        logger.warning(f"Model not available: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"ASR error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ASR engine error: {str(e)}")
    finally:
        # Cleanup temp files
        for path in [tmp_path, normalized]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    # Format response
    if response_format == "text":
        return Response(content=result.text, media_type="text/plain")

    elif response_format == "verbose_json":
        resp = {
            "text": result.text,
            "language": result.language,
            "duration": result.duration,
        }
        if result.words:
            resp["words"] = [
                {"start": w.start_time, "end": w.end_time, "word": w.text}
                for w in result.words
            ]
        return Response(content=json.dumps(resp, ensure_ascii=False), media_type="application/json")

    elif response_format == "json":
        return Response(
            content=json.dumps({"text": result.text}, ensure_ascii=False),
            media_type="application/json"
        )

    else:
        return Response(content=result.text, media_type="text/plain")


@router.post("/alignment")
async def align(
    file: UploadFile = File(...),
    model: str = "qwen3-asr",
    language: str | None = Query(default=None),
):
    """Word-level alignment endpoint — delegates to transcriptions with verbose_json."""
    # Reuse the transcription logic but force verbose_json format
    tmp_path = None
    normalized = None
    try:
        fd, tmp_path = tempfile.mkstemp()
        os.close(fd)

        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)

        normalized = normalize_audio(tmp_path)

        engine = EngineFactory.get_asr_engine()
        with open(normalized, "rb") as f:
            audio_bytes = f.read()

        result = engine.transcribe(audio_bytes, language=language)

    except ModelNotAvailableError as e:
        logger.warning(f"Model not available: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alignment error: {str(e)}")
    finally:
        for path in [tmp_path, normalized]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    resp = {
        "text": result.text,
        "language": result.language,
        "duration": result.duration,
        "words": [
            {"word": w.text, "start": w.start_time, "end": w.end_time}
            for w in result.words
        ],
    }
    return Response(content=json.dumps(resp, ensure_ascii=False), media_type="application/json")
