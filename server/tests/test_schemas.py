"""Tests for Pydantic schemas."""

from src.schemas.audio import TTSRequest, ASRResponse, WordTimestampSchema, ModelResponse


def test_tts_request_defaults():
    req = TTSRequest(input="hello")
    assert req.model == "qwen3-tts"
    assert req.voice is None
    assert req.emotion is None
    assert req.language == "Auto"
    assert req.response_format == "wav"
    assert req.mode == "custom_voice"


def test_tts_request_full():
    req = TTSRequest(
        input="hello world",
        voice="Vivian",
        emotion="happy",
        language="English",
        response_format="mp3",
        mode="custom_voice",
    )
    assert req.voice == "Vivian"
    assert req.emotion == "happy"
    assert req.language == "English"
    assert req.response_format == "mp3"
    assert req.mode == "custom_voice"


def test_tts_request_voice_clone():
    req = TTSRequest(
        input="hello",
        mode="voice_clone",
        ref_audio="/path/to/ref.wav",
    )
    assert req.mode == "voice_clone"
    assert req.ref_audio == "/path/to/ref.wav"


def test_tts_request_voice_design():
    req = TTSRequest(
        input="hello",
        mode="voice_design",
        instruct="温柔的女声，音调偏高",
    )
    assert req.mode == "voice_design"
    assert req.instruct == "温柔的女声，音调偏高"


def test_asr_response_defaults():
    resp = ASRResponse(text="hello world")
    assert resp.text == "hello world"
    assert resp.language is None
    assert resp.duration is None
    assert resp.words is None


def test_asr_response_full():
    words = [WordTimestampSchema(word="hello", start=0.1, end=0.5)]
    resp = ASRResponse(
        text="hello world", language="en", duration=1.5, words=words,
    )
    assert resp.language == "en"
    assert resp.duration == 1.5
    assert len(resp.words) == 1


def test_model_response_defaults():
    resp = ModelResponse(id="qwen3-tts-1.7B")
    assert resp.id == "qwen3-tts-1.7B"
    assert resp.object == "model"
    assert isinstance(resp.created, int)
    assert resp.owned_by == "qwen3-voice-service"
