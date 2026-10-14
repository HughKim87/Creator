"""Measure cold, memory, and persistent prompt reuse with public reference only."""
import importlib.util
import json
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("local_qwen", root / "extension/src/qwen_tts_local.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
verification = app.RUNTIME / "verification"
temporary_cache = tempfile.TemporaryDirectory(dir=verification, prefix="cache-benchmark-")
cache_dir = Path(temporary_cache.name)
model = app.load_model()
calls = [0]
original = model.create_voice_clone_prompt
def counted(*args, **kwargs):
    calls[0] += 1
    return original(*args, **kwargs)
model.create_voice_clone_prompt = counted
cache = app.VoicePromptCache(cache_dir, app.VOICE_NAMESPACE)
from prepare_qwen_test_reference import public_reference
reference, transcript = public_reference(verification)
rows, outputs = [], []
for mode in ["first", "memory", "disk"]:
    if mode == "disk":
        cache = app.VoicePromptCache(cache_dir, app.VOICE_NAMESPACE)
    app.torch.manual_seed(42)
    print(f"Testing {mode} reuse...", flush=True)
    sr, wave = app.clone(model, reference if mode == "first" else None,
                         transcript if mode == "first" else "",
                         "안녕하세요. 저장된 목소리로 다시 읽습니다.", cache=cache)
    rows.append({"mode": mode, **app.LAST_METRICS, "duration_seconds": round(len(wave)/sr, 2)})
    outputs.append(wave)
assert calls[0] == 1, "Voice features must be extracted only once"
assert rows[1]["cache"] == "memory" and rows[2]["cache"] == "disk"
assert all(app.np.isfinite(x).all() and len(x) > 0 for x in outputs)
evidence = {"scope": "Public reference; same seed/script; new cache instance simulates process restart",
            "feature_extractions": calls[0], "runs": rows,
            "same_waveform": all(app.np.array_equal(outputs[0], x) for x in outputs[1:])}
(verification / "cache-benchmark.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
print(json.dumps(evidence, indent=2), flush=True)
temporary_cache.cleanup()
