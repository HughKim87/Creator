"""Public-sample functional verification, not user-voice quality evaluation."""
import importlib.util
import json
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("local_qwen", root / "extension/src/qwen_tts_local.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
import soundfile as sf

verification = app.RUNTIME / "verification"
from prepare_qwen_test_reference import public_reference
reference, transcript = public_reference(verification)
start = time.perf_counter()
print("Loading local model...", flush=True)
model = app.load_model()
load_seconds = time.perf_counter() - start
print(f"Loaded in {load_seconds:.2f}s; generating Korean sample...", flush=True)
start = time.perf_counter()
sample_rate, wave = app.clone(
    model, reference, transcript,
    "안녕하세요. 지금 이 컴퓨터에서 한국어 음성을 생성하고 있습니다.",
    cache=app.VoicePromptCache(verification / "public-test-cache", app.VOICE_NAMESPACE),
)
generation_seconds = time.perf_counter() - start
sf.write(verification / "korean-smoke.wav", wave, sample_rate)
evidence = {
    "reference": "Official Qwen public example; English reference, Korean synthesis",
    "scope": "Functional synthesis only; user voice similarity and perceptual quality not tested",
    "torch": app.torch.__version__,
    "gpu": app.torch.cuda.get_device_name(0),
    "model": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "load_seconds": round(load_seconds, 2),
    "generation_seconds": round(generation_seconds, 2),
    "sample_rate": sample_rate,
    "duration_seconds": round(len(wave) / sample_rate, 2),
    "finite": bool(app.np.isfinite(wave).all()),
    "peak": float(app.np.max(app.np.abs(wave))),
    "gpu_peak_allocated_mib": round(app.torch.cuda.max_memory_allocated() / 1024**2, 1),
}
assert evidence["finite"] and evidence["duration_seconds"] > 0 and evidence["peak"] > 0
(verification / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(evidence, ensure_ascii=False, indent=2))
