"""Local Korean Qwen voice-cloning UI. No remote inference or uploads."""
from __future__ import annotations

import os
import sys
import json
import urllib.request
import webbrowser
import threading
import time
from pathlib import Path
from tts_build import is_current, source_version

ROOT = Path(__file__).resolve().parents[2]
from creator_workspace import runtime_path, current_job_paths
RUNTIME = runtime_path("qwen-tts", ROOT)
JOB = current_job_paths(ROOT)
STATE = JOB["work"] / "tts" if JOB else RUNTIME
MODEL_DIR = RUNTIME / "models" / "Qwen3-TTS-12Hz-0.6B-Base"
os.environ.update({
    "HF_HOME": str(RUNTIME / "hf-cache"),
    "HF_HUB_OFFLINE": "1",
    "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "GRADIO_ANALYTICS_ENABLED": "False",
    "GRADIO_TEMP_DIR": str(STATE / "audio-temp"),
    "NUMBA_CACHE_DIR": str(RUNTIME / "numba-cache"),
    "TORCH_HOME": str(RUNTIME / "torch-cache"),
    "PYTHONDONTWRITEBYTECODE": "1",
})

# Reopening the launcher should use the already running app, not load two models.
if "--open-browser" in sys.argv:
    try:
        with urllib.request.urlopen("http://127.0.0.1:7865/config", timeout=2) as response:
            config = json.load(response)
        if any(c.get("props", {}).get("value", "").startswith("# 내 목소리로 대본 읽기")
               for c in config.get("components", [])
               if isinstance(c.get("props", {}).get("value", ""), str)):
            if not is_current(config):
                raise RuntimeError('TTS 서버가 이전 코드로 실행 중입니다. TTS 실행 콘솔에서 Ctrl+C로 종료한 뒤 다시 실행하세요.')
            webbrowser.open("http://127.0.0.1:7865")
            sys.exit(0)
    except (OSError, ValueError):
        pass

import gradio as gr
import numpy as np
import torch
from qwen_tts import Qwen3TTSModel
from transformers import StoppingCriteria, StoppingCriteriaList
sys.path.insert(0, str(Path(__file__).resolve().parent))
from qwen_reference import prepare_reference, read_srt_file
from qwen_voice_cache import VoicePromptCache

CANCEL = threading.Event()
VOICE_NAMESPACE = "qwen-0.6b-5d83992436eae1d760afd27aff78a71d676296fc-bf16-ref20-60-v2"
VOICE_CACHE = VoicePromptCache(STATE / "voice-prompts", VOICE_NAMESPACE)
LAST_METRICS = {}


class GenerationLimit(StoppingCriteria):
    def __init__(self):
        self.deadline = time.monotonic() + 180
        self.timed_out = False

    def __call__(self, input_ids, scores, **kwargs):
        self.timed_out = time.monotonic() > self.deadline
        return self.timed_out or CANCEL.is_set()


def load_model():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU를 사용할 수 없습니다. 전용 환경을 확인하세요.")
    return Qwen3TTSModel.from_pretrained(
        str(MODEL_DIR), device_map="cuda:0", dtype=torch.bfloat16,
        attn_implementation="sdpa",
    )


def register_voice(model, reference, transcript, progress=None, cache=None):
    cache = cache or VOICE_CACHE
    def build():
        if progress:
            progress(None, desc="처음 한 번: 목소리 특징 추출 중")
        reference_audio, cleaned_text, notice = prepare_reference(reference, transcript)
        return model.create_voice_clone_prompt(ref_audio=reference_audio, ref_text=cleaned_text), notice
    started = time.perf_counter()
    prompts, notice, hit = cache.acquire(reference, (transcript or "").strip(), build)
    seconds = time.perf_counter() - started
    return prompts, notice, hit, seconds


def clone(model, reference, transcript, script, progress=None, cache=None):
    transcript = (transcript or "").strip()
    script = (script or "").strip()
    if not script:
        raise gr.Error("새로 읽을 대본을 입력하세요.")
    CANCEL.clear()
    try:
        if progress:
            progress(0.05, desc="녹음 길이와 자막 확인 중")
        prompts, notice, hit, preparation_seconds = register_voice(model, reference, transcript, progress, cache)
        if progress:
            gr.Info("목소리 등록 완료. 다음부터 대본만 입력하세요." if hit == "created" else "저장된 목소리를 재사용합니다.")
            progress(None, desc="음성 생성 중 · 최대 3분 · 중단 가능")
        limit = GenerationLimit()
        generated_at = time.perf_counter()
        with torch.inference_mode():
            waves, sample_rate = model.generate_voice_clone(
                text=script, language="Korean", voice_clone_prompt=prompts, max_new_tokens=2048,
                stopping_criteria=StoppingCriteriaList([limit]),
            )
        if CANCEL.is_set():
            raise gr.Error("생성을 중단했습니다. 녹음과 대본은 그대로 유지됩니다.")
        if limit.timed_out:
            raise gr.Error("생성이 3분을 넘겨 중단했습니다. 더 짧은 대본으로 다시 시도하세요.")
        wave = np.asarray(waves[0], dtype=np.float32)
        if wave.size == 0 or not np.isfinite(wave).all():
            raise RuntimeError("Invalid generated waveform")
        LAST_METRICS.clear()
        LAST_METRICS.update(cache=hit, preparation_seconds=round(preparation_seconds, 4),
                            generation_seconds=round(time.perf_counter()-generated_at, 2))
        return (sample_rate, wave)
    except ValueError as exc:
        raise gr.Error(str(exc)) from None
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        raise gr.Error("GPU 메모리가 부족합니다. 다른 GPU 프로그램을 닫고 짧은 대본으로 다시 시도하세요.") from None


def main():
    from tts_engines import EngineManager, ENGINES
    from voxcpm_local import voice_directory
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / "ui.pid").write_text(str(os.getpid()), encoding="ascii")
    manager = EngineManager()
    qwen_help = "Qwen: 목소리 등록에는 **최소 20초 녹음**이 필요합니다. **20~60초는 전체를 사용**하고, 긴 녹음은 SRT 문장 경계에 맞춰 **최대 60초까지 사용**합니다."
    sovits_help = "GPT-SoVITS V5 Turbo: **3~10초 녹음과 해당 발화문**, 또는 **긴 녹음과 일치하는 SRT**를 넣으세요. 긴 녹음에서는 완전한 문장 구간을 선택합니다. 현재는 참고 음성 복제 방식이며 전용 학습 모델은 아닙니다."
    voxcpm_help = "VoxCPM2: **3~30초의 깨끗한 녹음**을 넣으세요. 발화문은 선택이며, 정확한 발화문을 함께 넣으면 음성과 발화문을 모두 참고합니다. 긴 녹음에는 **같은 녹음의 SRT**를 넣으면 3~10초의 완전한 문장 구간을 선택합니다."
    engine_help = {'Qwen': qwen_help, 'GPT-SoVITS': sovits_help, 'VoxCPM2': voxcpm_help}
    def saved_status(engine):
        if engine == 'Qwen':
            exists = VOICE_CACHE.active_key()
        elif engine == 'VoxCPM2':
            exists = (voice_directory() / 'active.json').is_file()
        else:
            exists = ((JOB['work'] / 'tts/gpt-sovits' if JOB else runtime_path('gpt-sovits', ROOT)) / 'voices/active.json').is_file()
        return f"**{engine} 저장된 목소리 사용 가능 — 새 대본만 입력하세요.**" if exists else f"{engine} 목소리를 한 번 등록하면 이후에는 대본만 입력하면 됩니다. 엔진별로 따로 저장됩니다."
    initial_engine = os.environ.get('TTS_DEFAULT_ENGINE', 'Qwen')
    if initial_engine not in ENGINES:
        initial_engine = 'Qwen'
    with gr.Blocks(title="내 목소리 · Qwen / GPT-SoVITS / VoxCPM2", analytics_enabled=False) as app:
        gr.Markdown("# 내 목소리로 대본 읽기\n한국어 녹음과 대본을 이 PC에서 처리합니다.")
        gr.Markdown(source_version(), elem_id='tts-source-version', visible=False)
        engine = gr.Radio(list(ENGINES), value=initial_engine, label='음성 엔진 선택')
        help_text = gr.Markdown(engine_help[initial_engine])
        saved = gr.Markdown(saved_status(initial_engine))
        previous_reference = os.environ.get("QWEN_PREVIOUS_REFERENCE")
        if previous_reference:
            previous_reference_path = Path(previous_reference).resolve()
            if not previous_reference_path.is_relative_to(STATE.resolve()) or not previous_reference_path.is_file():
                previous_reference = None
        reference = gr.Audio(value=previous_reference, label="1. 본인 목소리 녹음", sources=["upload", "microphone"], type="filepath")
        previous_srt = os.environ.get('QWEN_PREVIOUS_SRT')
        if previous_srt:
            srt_path = Path(previous_srt).resolve()
            if not srt_path.is_relative_to(STATE.resolve()) or not srt_path.is_file():
                previous_srt = None
        srt_file = gr.File(value=previous_srt, label="녹음의 SRT 파일 (선택)", file_types=[".srt"], type="filepath")
        srt_notice = gr.Markdown("SRT 파일을 넣으면 아래 녹음 내용이 자동으로 채워집니다.")
        transcript = gr.Textbox(value=read_srt_file(previous_srt) if previous_srt else '', label="2. 녹음에서 말한 내용", lines=3,
                                placeholder="녹음과 일치하는 발화문 또는 SRT 전체를 입력하세요.")
        def load_srt(path):
            try:
                text = read_srt_file(path)
                return text, "**SRT 파일을 불러왔습니다.** 녹음과 같은 자막인지 확인한 뒤 목소리를 등록하세요."
            except ValueError as exc:
                raise gr.Error(str(exc)) from None
        srt_file.upload(load_srt, inputs=[srt_file], outputs=[transcript,srt_notice], api_name="load_srt", queue=False)
        script = gr.Textbox(label="3. 새로 읽을 대본", lines=5,
                           placeholder="긴 대본도 입력하세요. 문장 단위로 나누어 생성한 뒤 하나의 음성으로 연결합니다.")
        script_count = gr.Markdown('현재 **0자** · 공백·줄바꿈 포함')
        script.change(
            fn=None, inputs=[script], outputs=[script_count], queue=False,
            js="(text) => `현재 **${Array.from((text || '').replace(/\\r\\n?/g, '\\n')).length.toLocaleString('ko-KR')}자** · 공백·줄바꿈 포함`",
        )
        save = gr.Button("목소리 등록 / 변경")
        button = gr.Button("내 목소리로 생성", variant="primary")
        stop = gr.Button("생성 중단")
        previous_audio = os.environ.get("QWEN_PREVIOUS_AUDIO")
        if previous_audio:
            previous_path = Path(previous_audio).resolve()
            if not previous_path.is_relative_to(STATE.resolve()) or not previous_path.is_file():
                previous_audio = None
        result = gr.Audio(value=previous_audio, label="생성된 음성 · 재생 / 다운로드", format="wav")
        timing = gr.Markdown()
        gr.Markdown("녹음은 외부 서비스로 전송되지 않으며, 임시 음성 파일은 이 PC의 전용 폴더에 남습니다.")
        def generate(e, a, b, c, progress=gr.Progress()):
            try:
                metrics = manager.run(e, 'generate', a, b, c, progress)
                return metrics['audio'], f"{e} · {metrics['chunks']}개 구간 완료 · 준비 {metrics['preparation_seconds']:.3f}초 · 음성 생성 {metrics['generation_seconds']:.1f}초", saved_status(e)
            except ValueError as exc:
                raise gr.Error(str(exc)) from None
        def save_voice(e, a, b, progress=gr.Progress()):
            try:
                metrics = manager.run(e, 'register', a, b, progress=progress)
                return f"**{e} 목소리 저장됨.** {metrics['notice']} · 준비 {metrics['preparation_seconds']:.3f}초. 이후 대본만 입력하세요."
            except ValueError as exc:
                raise gr.Error(str(exc)) from None
        def switch_engine(e):
            manager.stop()
            return engine_help[e], saved_status(e), None, ''
        engine.change(switch_engine, inputs=[engine], outputs=[help_text,saved,result,timing], concurrency_limit=1, concurrency_id='tts_gpu')
        save.click(save_voice, inputs=[engine, reference, transcript], outputs=[saved], concurrency_limit=1, concurrency_id="tts_gpu", api_name='register_voice')
        button.click(generate, inputs=[engine, reference, transcript, script], outputs=[result,timing,saved], concurrency_limit=1, concurrency_id="tts_gpu", api_name='generate_voice')
        stop.click(manager.cancel, inputs=[], outputs=[], queue=False)
    app.queue(max_size=1).launch(server_name="127.0.0.1", server_port=7865,
                                share=False, inbrowser="--open-browser" in sys.argv, show_error=False)


if __name__ == "__main__":
    main()
