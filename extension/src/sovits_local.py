"""Local GPT-SoVITS adapter with persisted reference audio and transcript."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from qwen_reference import TIME_LINE, seconds

ROOT = Path(__file__).resolve().parents[2]
from creator_workspace import runtime_path, current_job_paths
RUNTIME = runtime_path("gpt-sovits", ROOT)
JOB = current_job_paths(ROOT)
STATE = JOB["work"] / "tts/gpt-sovits" if JOB else RUNTIME


def select_sovits_reference(duration, transcript):
    text = (transcript or '').strip()
    if not text:
        raise ValueError('GPT-SoVITS에는 녹음과 일치하는 발화문 또는 SRT가 필요합니다.')
    cues = []
    for block in re.split(r'\n\s*\n', text.replace('\r', '')):
        lines = block.splitlines()
        for i, line in enumerate(lines):
            match = TIME_LINE.match(line.strip())
            if match:
                a, b = map(seconds, match.groups())
                words = ' '.join(lines[i+1:]).strip()
                if not words or a < 0 or b <= a or b > duration + 0.1 or (cues and a < cues[-1][1]):
                    raise ValueError('SRT 시간과 녹음 구간을 확인하세요.')
                cues.append((a, b, words))
                break
    if cues:
        for i, cue in enumerate(cues):
            selected = []
            for other in cues[i:]:
                length = other[1] - cue[0]
                if length > 9.9:
                    break
                selected.append(other[2])
                if length >= 3:
                    return cue[0], other[1], ' '.join(selected)
        raise ValueError('SRT에서 3~10초 길이의 완전한 문장 구간을 선택할 수 없습니다.')
    if '-->' in text or not 3 <= duration <= 9.9:
        raise ValueError('GPT-SoVITS는 3~10초 녹음과 해당 발화문, 또는 긴 녹음과 일치하는 SRT를 넣어주세요.')
    return 0, duration, text


class SovitsVoice:
    def __init__(self, directory=None):
        self.directory = Path(directory or STATE / 'voices')
        self.directory.mkdir(parents=True, exist_ok=True)

    def register(self, reference, transcript):
        if not reference:
            active = self.directory / 'active.json'
            if not active.is_file():
                raise ValueError('GPT-SoVITS 목소리를 먼저 등록하세요. Qwen 목소리와 별도로 저장됩니다.')
            record = json.loads(active.read_text(encoding='utf-8'))
            if not (self.directory / record['audio']).is_file():
                raise ValueError('저장된 참고 음성이 없습니다. 다시 등록하세요.')
            return record, '저장된 GPT-SoVITS 목소리 재사용'
        probe = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(reference)],
                               capture_output=True, check=True, timeout=15)
        duration = float(json.loads(probe.stdout)['format']['duration'])
        start, end, words = select_sovits_reference(duration, transcript)
        digest = hashlib.sha256(Path(reference).read_bytes() + words.encode() + f'{start}:{end}:v5turbo'.encode()).hexdigest()
        audio = self.directory / (digest + '.wav')
        if not audio.is_file():
            subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(reference),'-ss',str(start),'-t',str(end-start),
                            '-ac','1','-ar','32000',str(audio)], capture_output=True, check=True, timeout=30)
        record = {'audio': audio.name, 'text': words, 'start': start, 'end': end}
        pending = self.directory / 'active.pending'
        pending.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
        pending.replace(self.directory / 'active.json')
        return record, f'GPT-SoVITS 참고 녹음 {start:.2f}~{end:.2f}초 저장'


def configure_language_detector(repo):
    """Replace upstream's auto-download detector with an installed local model."""
    import importlib
    import fast_langdetect
    # This import sets upstream's global detector; override it afterwards and
    # before the TTS module can perform language detection during initialization.
    importlib.import_module('text.LangSegmenter')
    full = Path(repo) / 'GPT_SoVITS/pretrained_models/fast_langdetect/lid.176.bin'
    bundled = Path(fast_langdetect.__file__).parent / 'resources/lid.176.ftz'
    model = full if full.is_file() else bundled
    if not model.is_file():
        raise ValueError('설치된 언어 감지 모델이 없습니다. fast-langdetect의 로컬 모델을 확인하세요.')
    detector = fast_langdetect.LangDetector(
        fast_langdetect.LangDetectConfig(custom_model_path=str(model)))
    fast_langdetect.infer._default_detector = detector
    return detector


def load_pipeline():
    # The engine saves its configuration while loading, before voice registration.
    STATE.mkdir(parents=True, exist_ok=True)
    import os
    import sys
    import shutil
    import jieba
    import jieba.posseg
    # API-compatible pure Python variant avoids a system C++ compiler on Windows.
    sys.modules['jieba_fast'] = jieba
    sys.modules['jieba_fast.posseg'] = jieba.posseg
    from g2pk2 import G2p
    from mecab import MeCab
    G2p.check_mecab = lambda self: None
    G2p.get_mecab = lambda self: MeCab()
    repo = RUNTIME / 'repo'
    os.chdir(repo)
    sys.path[:0] = [str(repo), str(repo / 'GPT_SoVITS')]
    from tools import portable_runtime
    portable_runtime.FFMPEG_EXE = Path(shutil.which('ffmpeg'))
    portable_runtime.FFPROBE_EXE = Path(shutil.which('ffprobe'))
    configure_language_detector(repo)
    from TTS_infer_pack.TTS import TTS, TTS_Config
    weights = repo / 'GPT_SoVITS/pretrained_models'
    config = TTS_Config({'custom': {
        'device': 'cuda', 'is_half': True, 'version': 'v5turbo',
        't2s_weights_path': str(weights / 's1v3.ckpt'),
        'vits_weights_path': str(weights / 'gsv-v5-pretrained/s2Gv5turbo.pth'),
        'bert_base_path': str(weights / 'chinese-roberta-wwm-ext-large'),
        'cnhuhbert_base_path': str(weights / 'chinese-hubert-base'),
    }})
    config.configs_path = str(STATE / 'tts-infer.yaml')
    return TTS(config)
