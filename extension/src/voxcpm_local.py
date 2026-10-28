"""VoxCPM2 adapter. External installation/model inputs stay read-only.

API: OpenBMB VoxCPM 2.0.3, https://github.com/OpenBMB/VoxCPM
Reference copies, configuration and generated audio belong to the selected job.
"""
import hashlib
import json
import math
import subprocess
from pathlib import Path

from creator_workspace import runtime_path, current_job_paths
from qwen_reference import TIME_LINE
from sovits_local import select_sovits_reference

ROOT = Path(__file__).resolve().parents[2]


def configured_paths(root=ROOT):
    runtime = runtime_path('voxcpm2', root)
    config = runtime / 'installation.json'
    if not config.is_file():
        raise ValueError('VoxCPM2 연결 설정이 없습니다. configure_voxcpm2.py로 기존 설치 경로를 연결하세요.')
    record = json.loads(config.read_text(encoding='utf-8'))
    if record.get('schema_version') != 'creator-voxcpm2-installation-v1':
        raise ValueError('VoxCPM2 연결 설정 형식을 확인하세요.')
    python, model = Path(record['python']), Path(record['model'])
    if not python.is_absolute() or not python.is_file():
        raise ValueError('VoxCPM2 실행용 Python을 찾을 수 없습니다. 설치 경로를 다시 연결하세요.')
    if not model.is_absolute() or not (model / 'config.json').is_file():
        raise ValueError('VoxCPM2 모델을 찾을 수 없습니다. 모델 경로를 다시 연결하세요.')
    return python, model


def voice_directory(root=ROOT):
    job = current_job_paths(root)
    state = job['work'] / 'tts/voxcpm2' if job else runtime_path('voxcpm2', root)
    return state / 'voices'


def select_voxcpm_reference(duration, transcript):
    if not math.isfinite(duration) or duration < 3:
        raise ValueError('VoxCPM2에는 3초 이상의 참고 녹음을 넣어주세요.')
    text = (transcript or '').strip()
    if any(TIME_LINE.match(line.strip()) for line in text.splitlines()) or '-->' in text:
        # Whole SRT sentences, never combine the full transcript with a cropped clip.
        return select_sovits_reference(duration, text)
    if duration > 30:
        raise ValueError('30초보다 긴 녹음에는 일치하는 SRT를 넣거나 3~30초 구간을 선택해주세요.')
    return 0.0, duration, text


class VoxCPMVoice:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else voice_directory()
        self.directory.mkdir(parents=True, exist_ok=True)

    def register(self, reference, transcript):
        active = self.directory / 'active.json'
        if not reference:
            if not active.is_file():
                raise ValueError('VoxCPM2 목소리를 먼저 등록하세요. 엔진별로 따로 저장됩니다.')
            record = json.loads(active.read_text(encoding='utf-8'))
            name = record['audio']
            if Path(name).name != name or not (self.directory / name).is_file():
                raise ValueError('저장된 VoxCPM2 참고 음성을 찾을 수 없습니다. 다시 등록하세요.')
            return record, '저장된 VoxCPM2 목소리 재사용'
        probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                '-of', 'json', str(reference)], capture_output=True, check=True, timeout=15)
        duration = float(json.loads(probe.stdout)['format']['duration'])
        start, end, words = select_voxcpm_reference(duration, transcript)
        digest = hashlib.sha256(Path(reference).read_bytes() + words.encode('utf-8')
                                + f'{start}:{end}:voxcpm2-16k'.encode()).hexdigest()
        audio = self.directory / (digest + '.wav')
        if not audio.is_file():
            pending_audio = audio.with_suffix('.pending.wav')
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', str(start),
                            '-i', str(reference), '-t', str(end-start), '-ac', '1', '-ar', '16000',
                            str(pending_audio)], capture_output=True, check=True, timeout=30)
            pending_audio.replace(audio)
        record = {'audio': audio.name, 'text': words, 'start': start, 'end': end}
        pending = active.with_suffix('.pending')
        pending.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
        pending.replace(active)
        return record, f'VoxCPM2 참고 녹음 {start:.2f}~{end:.2f}초 저장'


def load_pipeline():
    _, directory = configured_paths()
    config = json.loads((directory / 'config.json').read_text(encoding='utf-8'))
    if config.get('architecture', '').lower() != 'voxcpm2':
        raise ValueError('VoxCPM2 모델 폴더를 선택하세요. VoxCPM 1.x는 지원하지 않습니다.')
    import torch
    from voxcpm import VoxCPM
    if not torch.cuda.is_available():
        raise ValueError('VoxCPM2용 CUDA GPU를 사용할 수 없습니다.')
    return VoxCPM.from_pretrained(str(directory), local_files_only=True,
                                  load_denoiser=False, optimize=False, device='cuda')


def ensure_context_capacity(model, reference, transcript, script):
    """Size both 2.0.3 KV caches for prefill AND generation, without editing weights.

    Mirrors VoxCPM2Model._encode_wav and the reference/continuation prefix layout.
    The local model may have a reduced max_length (512 rather than stock 8192).
    """
    import re
    import soundfile as sf
    pipeline = model.tts_model
    normalized_script = re.sub(r'\s+', ' ', script.replace('\n', ' '))
    text_tokens = len(pipeline.text_tokenizer(transcript + normalized_script))
    info = sf.info(reference)
    audio_tokens = math.ceil(info.frames * pipeline.audio_vae.sample_rate /
                             (info.samplerate * pipeline.patch_size * pipeline.chunk_size))
    # Reference start/end + text audio-start, plus a second audio copy in continuation mode.
    prefix = text_tokens + 3 + audio_tokens * (2 if transcript else 1)
    generation = min(2048, len(pipeline.text_tokenizer(normalized_script)) * 6 + 10)
    required = prefix + generation + 1
    if required > 8192:
        raise ValueError('참고 음성의 발화문과 대본이 VoxCPM2 처리 범위를 넘습니다. 녹음과 일치하는 짧은 발화문을 사용하거나 대본을 나눠주세요.')
    capacity = max(512, 1 << (required - 1).bit_length())
    for language_model in (pipeline.base_lm, pipeline.residual_lm):
        if language_model.kv_cache.max_length < required:
            language_model.setup_cache(1, capacity, pipeline.device,
                                       next(language_model.parameters()).dtype)
    return prefix, required


def synthesize(model, voices, record, script):
    import numpy as np
    reference = str(voices.directory / record['audio'])
    ensure_context_capacity(model, reference, record['text'], script)
    options = dict(text=script, reference_wav_path=reference, cfg_value=2.0,
                   inference_timesteps=10, normalize=False, denoise=False,
                   retry_badcase=False, max_len=2048)
    if record['text']:
        options.update(prompt_wav_path=reference, prompt_text=record['text'])
    wave = np.asarray(model.generate(**options), dtype=np.float32)
    if wave.ndim != 1 or not wave.size or not np.isfinite(wave).all():
        raise ValueError('VoxCPM2가 유효한 음성을 생성하지 못했습니다.')
    return model.tts_model.sample_rate, wave
