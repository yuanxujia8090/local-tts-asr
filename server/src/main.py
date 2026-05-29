"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .core.config import settings
from .api.tts import router as tts_router
from .api.asr import router as asr_router

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Suppress noisy third-party logs
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

app = FastAPI(
    title="Qwen3 Voice Service",
    description="Local TTS/ASR service with OpenAI-compatible API",
    version="0.1.0",
)

# CORS — allow frontend dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(tts_router, prefix="/v1/audio")
app.include_router(asr_router, prefix="/v1/audio")


@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible /models endpoint."""
    from .schemas.audio import ModelResponse
    return {"data": [
        ModelResponse(id="qwen3-tts-1.7B"),
        ModelResponse(id="qwen3-asr-1.7B"),
    ], "object": "list"}


@app.get("/health")
async def health():
    return {"status": "ok", "engine_mode": settings.engine_mode}


