"""Serialize local GPU workers and terminate owned processes on cancellation."""
import atexit
import json
import os
import subprocess
import threading
import time
import uuid
import wave
import psutil
from tts_text import split_script
from creator_workspace import runtime_path, current_job_paths, Lease
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINES = {'Qwen': 'qwen-tts', 'GPT-SoVITS': 'gpt-sovits', 'VoxCPM2': 'voxcpm2'}


class EngineManager:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.process = None
        self.engine = None
        self.lock = threading.Lock()
        self.cancelled = threading.Event()
        self.process_lock = threading.Lock()
        self.log = None
        job = current_job_paths(self.root)
        self.jobs = job['work'] / 'tts/jobs' if job else self.root / 'extension/.runtime/qwen-tts/jobs'
        self.gpu_lease = None
        self.jobs.mkdir(parents=True, exist_ok=True)
        atexit.register(self.stop)

    def stop(self):
        with self.process_lock:
            process, self.process = self.process, None
            self.engine = None
            if process is not None:
                children = []
                if isinstance(process.pid, int):
                    try:
                        children = psutil.Process(process.pid).children(recursive=True)
                    except psutil.NoSuchProcess:
                        pass
                # Windows venv python.exe redirects to another Python process.
                # Wait for the entire owned subtree before loading another GPU model.
                for child in reversed(children):
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                _, remaining = psutil.wait_procs(children, timeout=5)
                for child in remaining:
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass
                psutil.wait_procs(remaining, timeout=5)
                if process.stdin:
                    process.stdin.close()
            if self.gpu_lease:
                self.gpu_lease.__exit__(None, None, None)
                self.gpu_lease = None
            if self.log:
                self.log.close()
                self.log = None

    def cancel(self):
        self.cancelled.set()
        self.stop()

    def _wait(self, path, timeout, progress=None, *, timeout_message=None):
        deadline = time.monotonic() + timeout
        while not path.is_file():
            if self.cancelled.is_set():
                raise ValueError('생성을 중단했습니다. 저장된 목소리는 유지됩니다.')
            if self.process is None or self.process.poll() is not None:
                raise ValueError('음성 엔진이 종료됐습니다. 다시 시도하세요.')
            if time.monotonic() > deadline:
                self.stop()
                raise ValueError(timeout_message or '처리 시간이 3분을 넘어 중단했습니다. 짧은 대본으로 다시 시도하세요.')
            time.sleep(0.1)
        if self.cancelled.is_set():
            raise ValueError('생성을 중단했습니다. 저장된 목소리는 유지됩니다.')
        result = json.loads(path.read_text(encoding='utf-8'))
        if not result['ok']:
            raise ValueError(result['error'])
        return result

    def _start(self, engine, progress=None):
        if engine not in ENGINES:
            raise ValueError('지원하는 음성 엔진을 선택하세요.')
        if self.engine == engine and self.process and self.process.poll() is None:
            return
        python = runtime_path(ENGINES[engine], self.root) / 'venv/Scripts/python.exe'
        if engine == 'VoxCPM2':
            from voxcpm_local import configured_paths
            python, _ = configured_paths(self.root)
        if not python.is_file():
            raise ValueError(f'{engine}가 설치되어 있지 않습니다.')
        self.stop()
        if progress:
            progress(None, desc=f'{engine} 모델 불러오는 중 · 처음 전환 시 잠시 걸립니다')
        if os.environ.get('CREATOR_GPU_LEASE_HELD') != '1':
            self.gpu_lease = Lease('gpu', self.root)
            try:
                self.gpu_lease.__enter__()
            except RuntimeError as exc:
                self.gpu_lease = None
                raise ValueError(str(exc)) from None
        ready = self.jobs / f'{uuid.uuid4().hex}-ready.json'
        environment = dict(os.environ, PYTHONUTF8='1', PYTHONWARNINGS='ignore',
                           TTS_OWNER_PID=str(os.getpid()),
                           MPLCONFIGDIR=str(self.jobs / 'matplotlib'))
        component = runtime_path(ENGINES[engine], self.root)
        environment.update(HF_HOME=str(component / 'hf-cache'),
                           TORCH_HOME=str(component / 'torch-cache'),
                           HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                           HF_HUB_DISABLE_IMPLICIT_TOKEN='1', HF_HUB_DISABLE_TELEMETRY='1',
                           PYTHONDONTWRITEBYTECODE='1')
        try:
            with self.process_lock:
                if self.cancelled.is_set():
                    raise ValueError('생성을 중단했습니다.')
                self.log = (self.jobs / 'worker-startup.log').open('a', encoding='utf-8')
                self.process = subprocess.Popen([str(python), '-B', str(self.root / 'extension/src/tts_worker.py'), engine, str(ready)],
                    cwd=self.root, env=environment, stdin=subprocess.PIPE, stdout=self.log, stderr=self.log,
                    text=True, encoding='utf-8', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                self.engine = engine
            startup_timeout = 600 if engine == 'VoxCPM2' else 180
            self._wait(ready, startup_timeout,
                       timeout_message=f'{engine} 모델 로딩이 {startup_timeout // 60}분을 넘어 중단했습니다. GPU와 모델 경로를 확인하세요.')
        except BaseException:
            self.stop()
            raise

    def run(self, engine, action, reference=None, transcript='', script='', progress=None):
        if action not in {'register', 'generate'}:
            raise ValueError('지원하지 않는 작업입니다.')
        script = (script or '').strip()
        if action == 'generate' and not script:
            raise ValueError('새로 읽을 대본을 입력하세요.')
        with self.lock:
            self.cancelled.clear()
            self._start(engine, progress)
            chunks = split_script(script) if action == 'generate' else ['']
            results = []
            for index, chunk in enumerate(chunks, 1):
                if self.cancelled.is_set():
                    raise ValueError('생성을 중단했습니다. 저장된 목소리는 유지됩니다.')
                if progress:
                    progress((index - 1) / len(chunks), desc=f'{engine} · ' + (
                        '목소리 등록 중' if action == 'register' else
                        f'{index}/{len(chunks)} 구간 생성 중 · 구간당 최대 3분 · 중단 가능'))
                try:
                    result = self._request(action, reference if index == 1 else None,
                                           transcript if index == 1 else '', chunk)
                except ValueError as exc:
                    if action == 'generate' and not self.cancelled.is_set():
                        raise ValueError(f'{index}/{len(chunks)} 구간 생성 실패: {exc}') from None
                    raise
                results.append(result)
            result = dict(results[-1])
            if action == 'generate':
                if len(results) > 1:
                    result['audio'] = str(self._join_audio(results))
                result['preparation_seconds'] = sum(r['preparation_seconds'] for r in results)
                result['generation_seconds'] = sum(r['generation_seconds'] for r in results)
                result['chunks'] = len(chunks)
            if progress:
                progress(1, desc='완료')
            if self.cancelled.is_set():
                raise ValueError('생성을 중단했습니다. 저장된 목소리는 유지됩니다.')
            return result

    def _request(self, action, reference, transcript, script):
        key = uuid.uuid4().hex
        response = self.jobs / f'{key}.json'
        audio = self.jobs / f'{key}.wav'
        job = {'action': action, 'reference': reference, 'transcript': transcript or '',
               'script': script, 'response': str(response), 'audio': str(audio)}
        with self.process_lock:
            if self.cancelled.is_set() or self.process is None:
                raise ValueError('생성을 중단했습니다.')
            self.process.stdin.write(json.dumps(job, ensure_ascii=False) + '\n')
            self.process.stdin.flush()
        return self._wait(response, 180)

    def _join_audio(self, results):
        """Stream PCM WAV segments into one download without loading all audio."""
        target = self.jobs / f'{uuid.uuid4().hex}.wav'
        pending = target.with_suffix('.pending.wav')
        with wave.open(str(pending), 'wb') as output:
            expected = None
            for result in results:
                with wave.open(str(result['audio']), 'rb') as source:
                    params = (source.getnchannels(), source.getsampwidth(), source.getframerate())
                    if expected is None:
                        expected = params
                        output.setnchannels(params[0])
                        output.setsampwidth(params[1])
                        output.setframerate(params[2])
                    elif params != expected:
                        raise ValueError('음성 구간의 오디오 형식이 달라 연결할 수 없습니다.')
                    while True:
                        if self.cancelled.is_set():
                            raise ValueError('생성을 중단했습니다. 저장된 목소리는 유지됩니다.')
                        frames = source.readframes(65536)
                        if not frames:
                            break
                        output.writeframesraw(frames)
        pending.replace(target)
        return target
