"""Tests for local_engine constants and helper functions."""

from src.engines.local_engine import (
    QWEN_SPEAKERS,
    QWEN_SPEAKER_INFO,
    QWEN_MLX_MODELS,
    QWEN_CUDA_MODELS,
    ASR_MODELS,
    ALIGNER_MODELS,
    _get_models_table,
)


def test_qwen_speakers_has_9_entries():
    assert len(QWEN_SPEAKERS) == 9


def test_qwen_speaker_info_has_all_speakers():
    for speaker in QWEN_SPEAKERS:
        assert speaker in QWEN_SPEAKER_INFO


def test_qwen_speaker_info_structure():
    """Each speaker info should have (chinese_name, desc_en, desc_cn, native_lang)."""
    vivian_info = QWEN_SPEAKER_INFO["Vivian"]
    assert len(vivian_info) == 4
    assert vivian_info[0] == "薇薇安"
    assert "Bright" in vivian_info[1]


def test_mlx_models_has_three_modes():
    for mode in ("custom_voice", "voice_design", "voice_clone"):
        assert mode in QWEN_MLX_MODELS


def test_cuda_models_has_three_modes():
    for mode in ("custom_voice", "voice_design", "voice_clone"):
        assert mode in QWEN_CUDA_MODELS


def test_asr_models_has_both_sizes():
    for backend in ("mlx", "cuda"):
        assert "1.7B" in ASR_MODELS[backend]
        assert "0.6B" in ASR_MODELS[backend]


def test_aligner_models_has_both_backends():
    assert "mlx" in ALIGNER_MODELS
    assert "cuda" in ALIGNER_MODELS


def test_get_models_table_returns_correct_table():
    """_get_models_table should return MLX table on macOS, CUDA on Linux."""
    from unittest.mock import patch

    with patch('src.engines.local_engine.get_backend', return_value="mlx"):
        table = _get_models_table()
        assert "voice_design" in table

    with patch('src.engines.local_engine.get_backend', return_value="cuda"):
        table = _get_models_table()
        assert "voice_design" in table
