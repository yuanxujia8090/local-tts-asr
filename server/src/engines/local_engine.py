"""Local engine implementations — MLX and PyTorch backends.

Adapted from opc-cli/scripts/tts/qwen_engine.py and opc-cli/scripts/asr/.
"""

import tempfile
import os
import threading

from .base import TTSEngine, ASREngine, WordTimestamp, ASRResult
from ..utils.platform import get_backend, check_mlx_available
from ..utils.model_path import resolve_model_path
from ..utils.punctuation import restore_punctuation


# ── Model mappings (adapted from opc-cli) ───────────────────────

QWEN_MLX_MODELS = {
    "custom_voice": {
        "1.7B": "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit",
        "0.6B": "mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit",
    },
    "voice_design": {
        "1.7B": "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-4bit",
    },
    "voice_clone": {
        "1.7B": "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit",
        "0.6B": "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit",
    },
}

QWEN_CUDA_MODELS = {
    "custom_voice": {
        "1.7B": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        "0.6B": "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    },
    "voice_design": {
        "1.7B": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    },
    "voice_clone": {
        "1.7B": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        "0.6B": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    },
}

QWEN_SPEAKERS = ["Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric",
                 "Ryan", "Aiden", "Ono_Anna", "Sohee"]

# Speaker info: (chinese_name, description_en, description_cn, native_language)
QWEN_SPEAKER_INFO = {
    "Vivian":    ("薇薇安",   "Bright, slightly edgy young female voice",
                  "明亮、略带棱角感的年轻女性声音", "Chinese 中文"),
    "Serena":    ("塞蕾娜",   "Warm, gentle young female voice",
                  "温暖、温柔的年轻女性声音", "Chinese 中文"),
    "Uncle_Fu":  ("傅叔叔",   "Seasoned male voice with a low, mellow timbre",
                  "成熟男性声音，音色低沉柔和", "Chinese 中文"),
    "Dylan":     ("迪伦",     "Youthful Beijing male voice with a clear, natural timbre",
                  "年轻北京男性声音，音质清晰自然", "Chinese (Beijing Dialect) 北京方言"),
    "Eric":      (None,       "Lively Chengdu male voice with a slightly husky brightness",
                  "活泼成都男性声音，略带沙哑的明亮感", "Chinese (Sichuan Dialect) 四川方言"),
    "Ryan":      ("瑞安",     "Dynamic male voice with strong rhythmic drive",
                  "富有节奏感的动态男声", "English 英语"),
    "Aiden":     ("艾登",     "Sunny American male voice with a clear midrange",
                  "阳光美国男性声音，中频清晰", "English 英语"),
    "Ono_Anna":  ("小野安娜", "Playful Japanese female voice with a light, nimble timbre",
                  "活泼的日语女性声音，音色轻快灵活", "Japanese 日语"),
    "Sohee":     (None,       "Warm Korean female voice with rich emotion",
                  "温暖感人的韩语女性声音", "Korean 韩语"),
}

# Language mapping for MLX (lang_code parameter)
_MLX_LANG_MAP = {
    "Auto": "auto", "Chinese": "chinese", "English": "english",
    "Japanese": "japanese", "Korean": "korean", "German": "german",
    "French": "french", "Russian": "russian", "Portuguese": "portuguese",
    "Spanish": "spanish", "Italian": "italian",
}

# ASR model mapping: size -> model_id
ASR_MODELS = {
    "mlx": {
        "1.7B": "mlx-community/Qwen3-ASR-1.7B-8bit",
        "0.6B": "mlx-community/Qwen3-ASR-0.6B-8bit",
    },
    "cuda": {
        "1.7B": "Qwen/Qwen3-ASR-1.7B",
        "0.6B": "Qwen/Qwen3-ASR-0.6B",
    },
}

ALIGNER_MODELS = {
    "mlx": "mlx-community/Qwen3-ForcedAligner-0.6B-8bit",
    "cuda": "Qwen/Qwen3-ForcedAligner-0.6B",
}

# Model cache (lazy-loaded singleton) — TTS models
_model_cache: dict[str, object] = {}  # type: ignore[assignment]
_model_lock = threading.Lock()

# ASR model cache — separate from TTS
_asr_model_cache: dict[str, object] = {}  # type: ignore[assignment]
_asr_model_lock = threading.Lock()


# ── TTS model loading (adapted from opc-cli) ───────────────────

def _get_cached_model(model_id: str) -> object:
    """Lazy-load and cache a model (singleton pattern, thread-safe)."""
    if model_id in _model_cache:
        return _model_cache[model_id]
    with _model_lock:
        if model_id not in _model_cache:
            _model_cache[model_id] = _load_model(model_id)  # type: ignore[assignment]
    return _model_cache[model_id]


def _load_model(model_id: str) -> object:
    """Load model based on current backend."""
    if get_backend() == "mlx":
        return _load_mlx_tts(model_id)
    return _load_cuda_tts(model_id)


def _load_mlx_tts(model_id: str):
    """Load Qwen3-TTS via MLX."""
    import json
    from mlx_audio.tts.utils import load_model

    path = resolve_model_path(model_id)
    print(f"[MLX-TTS] Loading {model_id} from {path}...")

    # Qwen3-TTS models store config fields nested under "talker_config"
    # and sometimes deeper in "code_predictor_config". mlx_audio expects
    # them at the top level of config.json. We patch the model_type to
    # "qwen3_tts" so mlx_audio routes to the correct model class.
    config_path = os.path.join(path, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)

        # Ensure model_type is qwen3_tts for mlx_audio routing
        if config.get("model_type") != "qwen3_tts":
            original_type = config.get("model_type")
            config["model_type"] = "qwen3_tts"
            print(f"  -> Patched model_type: {original_type} -> qwen3_tts")

        # Flatten talker_config fields to top level if missing
        tc = config.get("talker_config", {})
        if isinstance(tc, dict):
            for key, value in tc.items():
                if key not in config:
                    if isinstance(value, dict):
                        for k2, v2 in value.items():
                            if k2 not in config:
                                config[k2] = v2
                    else:
                        config[key] = value

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            print(f"  -> Flattened talker_config into top-level config")

    return load_model(path)


def _load_cuda_tts(model_id: str):
    """Load Qwen3-TTS via PyTorch/CUDA."""
    import torch
    from qwen_tts import Qwen3TTSModel
    path = resolve_model_path(model_id)
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"[CUDA-TTS] Loading {model_id} on {device}...")
    return Qwen3TTSModel.from_pretrained(path, device_map=device, dtype=torch.bfloat16)


def _get_models_table() -> dict:
    """Get the model table for the current backend."""
    if get_backend() == "mlx":
        return QWEN_MLX_MODELS
    return QWEN_CUDA_MODELS


# ── MLX TTS Engine (adapted from opc-cli) ─────────────────────

class MLXTTSEngine(TTSEngine):
    """Qwen3-TTS via MLX (Apple Silicon)."""

    def synthesize(self, text: str, voice: str | None = None,
                   emotion: str | None = None, language: str = "Auto",
                   ref_audio_path: str | None = None, **kwargs) -> bytes:

        mode = kwargs.get("mode") or "custom_voice"
        ref_text = kwargs.get("ref_text")
        instruct = kwargs.get("instruct", emotion)

        # Resolve saved custom voice ID to actual reference audio path
        if mode == "custom_voice" and voice and not self._is_builtin_speaker(voice):
            ref_audio_path = self._resolve_custom_voice(voice)
            if not ref_audio_path:
                raise ValueError(f"Custom voice '{voice}' not found")
            mode = "voice_clone"

        # Auto-infer mode from parameters if not explicitly set
        if mode == "custom_voice" and instruct and not voice:
            mode = "voice_design"

        # Collect generation kwargs
        gen_kwargs: dict = {}
        if "temperature" in kwargs and kwargs["temperature"] is not None:
            gen_kwargs["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs and kwargs["top_p"] is not None:
            gen_kwargs["top_p"] = kwargs["top_p"]
        if "max_new_tokens" in kwargs and kwargs["max_new_tokens"] is not None:
            gen_kwargs["max_new_tokens"] = kwargs["max_new_tokens"]

        models_table = _get_models_table()
        if mode not in models_table:
            raise ValueError(f"Unknown TTS mode '{mode}'. Available: {', '.join(models_table.keys())}")

        model_id = models_table[mode]["1.7B"]
        model = _get_cached_model(model_id)

        lang_code = _MLX_LANG_MAP.get(language, language.lower() if language else "auto")

        # Collect audio chunks
        audio_chunks = []
        sample_rate = None

        if mode == "custom_voice":
            if not voice:
                raise ValueError(f"voice is required for custom_voice mode. Available: {', '.join(QWEN_SPEAKERS)}")
            print(f"[MLX-TTS] Generating with CustomVoice: speaker={voice}, instruct={instruct}")
            try:
                generate_kwargs = dict(
                    text=text, voice=voice, lang_code=lang_code, verbose=True,
                )
                if instruct:
                    generate_kwargs["instruct"] = instruct
                if gen_kwargs:
                    generate_kwargs.update(gen_kwargs)
                for result in model.generate(**generate_kwargs):
                    import numpy as np
                    audio_chunks.append(np.array(result.audio))
                    sample_rate = result.sample_rate
            except Exception as e:
                raise RuntimeError(f"MLX TTS custom_voice generation failed: {e}") from e

        elif mode == "voice_design":
            if not instruct:
                raise ValueError("instruct (voice description) is required for voice_design mode")
            print(f"[MLX-TTS] Generating with VoiceDesign: instruct={instruct}")
            try:
                lang_code = _MLX_LANG_MAP.get(language, language.lower() if language else "auto")
                for result in model.generate_voice_design(
                    text=text, instruct=instruct, language=lang_code, verbose=True,
                ):
                    import numpy as np
                    audio_chunks.append(np.array(result.audio))
                    sample_rate = result.sample_rate
            except Exception as e:
                raise RuntimeError(f"MLX TTS voice_design generation failed: {e}") from e

        elif mode == "voice_clone":
            if not ref_audio_path:
                raise ValueError("ref_audio is required for voice_clone mode")
            print(f"[MLX-TTS] Generating with VoiceClone: ref_audio={ref_audio_path}")
            try:
                for result in model.generate(
                    text=text, ref_audio=ref_audio_path, ref_text=ref_text,
                    lang_code=lang_code, verbose=True,
                ):
                    import numpy as np
                    audio_chunks.append(np.array(result.audio))
                    sample_rate = result.sample_rate
            except Exception as e:
                raise RuntimeError(f"MLX TTS voice_clone generation failed: {e}") from e

        if not audio_chunks:
            raise RuntimeError("No audio generated by MLX engine")

        # Join chunks and write to bytes
        import mlx.core as mx
        if len(audio_chunks) > 1:
            audio = mx.concatenate([mx.array(chunk) for chunk in audio_chunks], axis=0)
        else:
            audio = mx.array(audio_chunks[0])

        # Write to temp WAV file, then read as bytes
        from mlx_audio.audio_io import write as audio_write
        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        audio_write(tmp_path, audio, sample_rate, format="wav")

        with open(tmp_path, "rb") as f:
            data = f.read()
        os.remove(tmp_path)

        return data

    @staticmethod
    def _is_builtin_speaker(voice: str) -> bool:
        """Check if voice is a built-in speaker name."""
        return voice in QWEN_SPEAKERS

    @staticmethod
    def _resolve_custom_voice(voice_id: str) -> str | None:
        """Resolve a saved custom voice ID to its reference audio path."""
        import json
        voices_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "custom_voices",
        )
        index_path = os.path.join(voices_dir, "voices.json")
        if not os.path.exists(index_path):
            return None
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                voices = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
        real_voices_dir = os.path.realpath(voices_dir)
        for v in voices:
            if v["id"] == voice_id:
                filepath = os.path.join(voices_dir, v["filename"])
                # Security: prevent path traversal
                real_path = os.path.realpath(filepath)
                if not real_path.startswith(real_voices_dir):
                    return None
                if os.path.exists(filepath):
                    return filepath
        return None


# ── PyTorch TTS Engine (adapted from opc-cli) ─────────────────

class PyTorchTTSEngine(TTSEngine):
    """Qwen3-TTS via PyTorch/CUDA (adapted from opc-cli)."""

    def synthesize(self, text: str, voice: str | None = None,
                   emotion: str | None = None, language: str = "Auto",
                   ref_audio_path: str | None = None, **kwargs) -> bytes:

        import soundfile as sf

        mode = kwargs.get("mode", "custom_voice")
        ref_text = kwargs.get("ref_text")
        instruct = kwargs.get("instruct", emotion)

        # Resolve saved custom voice ID to actual reference audio path
        if mode == "custom_voice" and voice and not self._is_builtin_speaker(voice):
            ref_audio_path = self._resolve_custom_voice(voice)
            if not ref_audio_path:
                raise ValueError(f"Custom voice '{voice}' not found")
            mode = "voice_clone"

        # Auto-infer mode from parameters if not explicitly set
        if not mode or mode == "custom_voice":
            if instruct and not voice:
                mode = "voice_design"

        models_table = _get_models_table()
        if mode not in models_table:
            raise ValueError(f"Unknown TTS mode '{mode}'. Available: {', '.join(models_table.keys())}")

        model_id = models_table[mode]["1.7B"]
        model = _get_cached_model(model_id)

        gen_kwargs = dict(
            max_new_tokens=4096, do_sample=True, top_k=50,
            top_p=1.0, temperature=0.9, repetition_penalty=1.05
        )
        # Override with user-provided generation parameters
        if "temperature" in kwargs and kwargs["temperature"] is not None:
            gen_kwargs["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs and kwargs["top_p"] is not None:
            gen_kwargs["top_p"] = kwargs["top_p"]
        if "max_new_tokens" in kwargs and kwargs["max_new_tokens"] is not None:
            gen_kwargs["max_new_tokens"] = kwargs["max_new_tokens"]

        fd, wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        if mode == "custom_voice":
            if not voice:
                raise ValueError(f"voice is required for custom_voice mode. Available: {', '.join(QWEN_SPEAKERS)}")
            if voice not in QWEN_SPEAKERS:
                raise ValueError(f"Unknown speaker '{voice}'. Available: {', '.join(QWEN_SPEAKERS)}")
            print(f"[CUDA-TTS] Generating with CustomVoice: speaker={voice}, instruct={instruct}")
            wavs, sr = model.generate_custom_voice(
                text=[text], speaker=[voice], language=[language],
                instruct=[instruct] if instruct else None, **gen_kwargs
            )

        elif mode == "voice_design":
            if not instruct:
                raise ValueError("instruct (voice description) is required for voice_design mode")
            print(f"[CUDA-TTS] Generating with VoiceDesign: instruct={instruct}")
            wavs, sr = model.generate_voice_design(
                text=[text], instruct=[instruct], language=[language], **gen_kwargs
            )

        elif mode == "voice_clone":
            if not ref_audio_path:
                raise ValueError("ref_audio is required for voice_clone mode")
            x_vector_only = not ref_text
            print(f"[CUDA-TTS] Generating with VoiceClone: ref_audio={ref_audio_path}")
            prompt_items = model.create_voice_clone_prompt(
                ref_audio=ref_audio_path, ref_text=ref_text, x_vector_only_mode=x_vector_only
            )
            wavs, sr = model.generate_voice_clone(
                text=[text], language=[language], voice_clone_prompt=prompt_items, **gen_kwargs
            )

        sf.write(wav_path, wavs[0], sr)

        with open(wav_path, "rb") as f:
            data = f.read()
        os.remove(wav_path)

        return data

    @staticmethod
    def _is_builtin_speaker(voice: str) -> bool:
        """Check if voice is a built-in speaker name."""
        return voice in QWEN_SPEAKERS

    @staticmethod
    def _resolve_custom_voice(voice_id: str) -> str | None:
        """Resolve a saved custom voice ID to its reference audio path."""
        import json
        voices_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "custom_voices",
        )
        index_path = os.path.join(voices_dir, "voices.json")
        if not os.path.exists(index_path):
            return None
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                voices = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
        real_voices_dir = os.path.realpath(voices_dir)
        for v in voices:
            if v["id"] == voice_id:
                filepath = os.path.join(voices_dir, v["filename"])
                # Security: prevent path traversal
                real_path = os.path.realpath(filepath)
                if not real_path.startswith(real_voices_dir):
                    return None
                if os.path.exists(filepath):
                    return filepath
        return None


# ── ASR model loading (adapted from opc-cli) ───────────────────

def _language_to_code(language: str | None) -> str | None:
    """Convert language name to code for MLX models."""
    if not language:
        return None
    mapping = {
        "chinese": "Chinese", "english": "English", "japanese": "Japanese",
        "korean": "Korean", "german": "German", "french": "French",
        "russian": "Russian",
    }
    lower = language.lower().strip()
    if lower in mapping:
        return mapping[lower]
    for code, name in mapping.items():
        if name.lower() == lower:
            return name
    return language.capitalize() if language else None


def _load_asr_mlx(model_id: str):
    """Load ASR model using MLX (Apple Silicon)."""
    from mlx_audio.stt.utils import load_model
    model_path = resolve_model_path(model_id)
    print(f"[MLX-ASR] Loading {model_id} via MLX...")
    return load_model(model_path)


def _load_aligner_mlx():
    """Load ForcedAligner model using MLX."""
    from mlx_audio.stt.utils import load_model
    model_path = resolve_model_path(ALIGNER_MODELS["mlx"])
    print(f"[MLX-ASR] Loading ForcedAligner ({ALIGNER_MODELS['mlx']}) via MLX...")
    return load_model(model_path)


def _load_asr_cuda(model_id: str, with_aligner: bool = True):
    """Load ASR model using CUDA/PyTorch."""
    import torch
    from qwen_asr import Qwen3ASRModel

    asr_path = resolve_model_path(model_id)
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    if with_aligner:
        aligner_path = resolve_model_path(ALIGNER_MODELS["cuda"])
        print(f"[CUDA-ASR] Loading Qwen3-ASR ({model_id}) + ForcedAligner on {device}...")
        return Qwen3ASRModel.from_pretrained(
            asr_path, dtype=torch.bfloat16, device_map=device,
            forced_aligner=aligner_path,
            forced_aligner_kwargs=dict(dtype=torch.bfloat16, device_map=device),
            max_inference_batch_size=8, max_new_tokens=4096,
        )
    else:
        print(f"[CUDA-ASR] Loading Qwen3-ASR ({model_id}) on {device}...")
        return Qwen3ASRModel.from_pretrained(
            asr_path, dtype=torch.bfloat16, device_map=device,
            max_inference_batch_size=8, max_new_tokens=4096,
        )


def _get_asr_mlx(model_id: str, with_aligner: bool = True) -> dict:
    """Load ASR model via MLX (thread-safe)."""
    cache_key = f"mlx_{model_id}_aligner_{with_aligner}"

    if cache_key in _asr_model_cache:
        return _asr_model_cache[cache_key]

    with _asr_model_lock:
        if cache_key not in _asr_model_cache:
            model = _load_asr_mlx(model_id)
            result: dict = {"asr": model}
            if with_aligner:
                result["aligner"] = _load_aligner_mlx()
            _asr_model_cache[cache_key] = result

    return _asr_model_cache[cache_key]


def _get_asr_cuda(model_id: str, with_aligner: bool = True) -> object:
    """Load ASR model via CUDA/PyTorch (thread-safe)."""
    cache_key = f"cuda_{model_id}_aligner_{with_aligner}"

    if cache_key in _asr_model_cache:
        return _asr_model_cache[cache_key]

    with _asr_model_lock:
        if cache_key not in _asr_model_cache:
            model = _load_asr_cuda(model_id, with_aligner=with_aligner)
            _asr_model_cache[cache_key] = model

    return _asr_model_cache[cache_key]


def _get_asr_model(model_id: str, with_aligner: bool = True) -> object:
    """Load and cache a Qwen3-ASR model with optional aligner (thread-safe).

    Auto-detects backend based on current environment.
    Prefers mlx if available on macOS, otherwise falls back to CUDA/PyTorch.
    """
    if check_mlx_available():
        return _get_asr_mlx(model_id, with_aligner=with_aligner)
    else:
        return _get_asr_cuda(model_id, with_aligner=with_aligner)


# ── ASR Engines (adapted from opc-cli) ────────────────────────

class MLXASREngine(ASREngine):
    """Qwen3-ASR via MLX (Apple Silicon)."""

    def __init__(self, model_size: str = "1.7B"):
        self.model_size = model_size

    def transcribe(self, audio_bytes: bytes, language: str | None = None) -> ASRResult:
        fd, audio_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            import soundfile as sf
            wav, sr = sf.read(audio_path, dtype="float32", always_2d=False)
            if wav.ndim > 1:
                import numpy as np
                wav = np.mean(wav, axis=1)
            duration = len(wav) / sr

            model_id = ASR_MODELS["mlx"][self.model_size]
            models_dict = _get_asr_model(model_id, with_aligner=True)  # type: ignore[assignment]
            asr_model = models_dict["asr"]
            aligner_model = models_dict["aligner"]

            print("[MLX-ASR] Step 1/2: Transcribing...")
            lang_code = _language_to_code(language) or "Chinese"
            asr_result = asr_model.generate(audio_path, language=lang_code, verbose=True)
            full_text = asr_result.text
            detected_language = lang_code

            if not full_text:
                return ASRResult(language=detected_language, text="", duration=duration, words=[])

            print(f"[MLX-ASR] Transcribed text ({len(full_text)} chars): {full_text[:100]}...")

            print("[MLX-ASR] Step 2/2: Forced alignment...")
            align_result = aligner_model.generate(
                audio=audio_path, text=full_text, language=detected_language,
            )

            words = [WordTimestamp(text=item.text, start_time=item.start_time, end_time=item.end_time)
                     for item in align_result]
            words = restore_punctuation(words, full_text)

            return ASRResult(language=detected_language, text=full_text, duration=duration, words=words)

        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)


class PyTorchASREngine(ASREngine):
    """Qwen3-ASR via PyTorch/CUDA (adapted from opc-cli)."""

    def __init__(self, model_size: str = "1.7B"):
        self.model_size = model_size

    def transcribe(self, audio_bytes: bytes, language: str | None = None) -> ASRResult:
        import soundfile as sf

        fd, audio_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            wav, sr = sf.read(audio_path, dtype="float32", always_2d=False)
            if wav.ndim > 1:
                import numpy as np
                wav = np.mean(wav, axis=1)
            duration = len(wav) / sr

            model_id = ASR_MODELS["cuda"][self.model_size]
            model = _get_asr_model(model_id, with_aligner=True)  # type: ignore[assignment]

            lang_code = _language_to_code(language)

            if duration > 300:
                print("[CUDA-ASR] Splitting audio into 30s chunks...")
                chunk_duration = 30.0
                segment_samples = int(chunk_duration * sr)

                all_words = []
                detected_language = None

                for i, start in enumerate(range(0, len(wav), segment_samples)):
                    end = min(start + segment_samples, len(wav))
                    offset = start / sr

                    print(f"[CUDA-ASR] Processing chunk {i+1}...")
                    results = model.transcribe(
                        audio=(wav[start:end], sr), language=lang_code, return_time_stamps=True,
                    )

                    if detected_language is None:
                        detected_language = results[0].language

                    chunk_words = []
                    if results[0].time_stamps:
                        for ts in results[0].time_stamps:
                            chunk_words.append(WordTimestamp(
                                text=ts.text, start_time=ts.start_time + offset, end_time=ts.end_time + offset,
                            ))

                    chunk_words = restore_punctuation(chunk_words, results[0].text)
                    all_words.extend(chunk_words)

                full_text = "".join(w.text for w in all_words)
                return ASRResult(language=detected_language or "unknown", text=full_text,
                                 duration=duration, words=all_words)

            else:
                print("[CUDA-ASR] Processing audio directly...")
                results = model.transcribe(audio=audio_path, language=lang_code, return_time_stamps=True)
                result = results[0]

                words = []
                if result.time_stamps:
                    for ts in result.time_stamps:
                        words.append(WordTimestamp(text=ts.text, start_time=ts.start_time, end_time=ts.end_time))

                words = restore_punctuation(words, result.text)
                return ASRResult(language=result.language, text=result.text, duration=duration, words=words)

        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)
