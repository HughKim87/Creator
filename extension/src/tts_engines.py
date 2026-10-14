"""Serialize local GPU workers and terminate owned processes on cancellation."""
import atexit
import json
import os
import subprocess
import threading
import time
import uuid
import psutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINES = {'Qwen': 'qwen-tts', 'GPT-SoVITS': 'gpt-sovits'}


class EngineManager:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.process = None
        self.engine = None
        self.lock = threading.Lock()
        self.cancelled = threading.Event()
        self.process_lock = threading.Lock()
        self.log = None
        self.jobs = self.root / 'extension/.runtime/qwen-tts/jobs'
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
            if self.log:
                self.log.close()
                self.log = None

    def cancel(self):
        self.cancelled.set()
        self.stop()

    def _wait(self, path, timeout, progress=None):
        deadline = time.monotonic() + timeout
        while not path.is_file():
            if self.cancelled.is_set():
                raise ValueError('생성을 중단했습니다. 저장된 목소리는 유지됩니다.')
            if self.process is None or self.process.poll() is not None:
                raise ValueError('음성 엔진이 종료됐습니다. 다시 시도하세요.')
            if time.monotonic() > deadline:
                self.stop()
                raise ValueError('처리 시간이 3분을 넘어 중단했습니다. 짧은 대본으로 다시 시도하세요.')
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
        python = self.root / 'extension/.runtime' / ENGINES[engine] / 'venv/Scripts/python.exe'
        if not python.is_file():
            raise ValueError(f'{engine}가 설치되어 있지 않습니다.')
        self.stop()
        if progress:
            progress(None, desc=f'{engine} 모델 불러오는 중 · 처음 전환 시 잠시 걸립니다')
        ready = self.jobs / f'{uuid.uuid4().hex}-ready.json'
        environment = dict(os.environ, PYTHONUTF8='1', PYTHONWARNINGS='ignore',
                           TTS_OWNER_PID=str(os.getpid()),
                           MPLCONFIGDIR=str(self.root / 'extension/.runtime/gpt-sovits/matplotlib'))
        with self.process_lock:
            if self.cancelled.is_set():
                raise ValueError('생성을 중단했습니다.')
            self.log = (self.jobs / 'worker-startup.log').open('a', encoding='utf-8')
            self.process = subprocess.Popen([str(python), '-B', str(self.root / 'extension/src/tts_worker.py'), engine, str(ready)],
                cwd=self.root, env=environment, stdin=subprocess.PIPE, stdout=self.log, stderr=self.log,
                text=True, encoding='utf-8', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.engine = engine
        try:
            self._wait(ready, 180)
        except Exception:
            self.stop()
            raise

    def run(self, engine, action, reference=None, transcript='', script='', progress=None):
        if action not in {'register', 'generate'}:
            raise ValueError('지원하지 않는 작업입니다.')
        if action == 'generate' and (not script.strip() or len(script.strip()) > 500):
            raise ValueError('새 대본은 1~500자로 입력하세요.')
        with self.lock:
            self.cancelled.clear()
            self._start(engine, progress)
            if progress:
                progress(None, desc=f'{engine} · ' + ('목소리 등록 중' if action == 'register' else '음성 생성 중 · 최대 3분 · 중단 가능'))
            key = uuid.uuid4().hex
            response = self.jobs / f'{key}.json'
            audio = self.jobs / f'{key}.wav'
            job = {'action': action, 'reference': reference, 'transcript': transcript or '',
                   'script': script.strip(), 'response': str(response), 'audio': str(audio)}
            with self.process_lock:
                if self.cancelled.is_set() or self.process is None:
                    raise ValueError('생성을 중단했습니다.')
                self.process.stdin.write(json.dumps(job, ensure_ascii=False) + '\n')
                self.process.stdin.flush()
            return self._wait(response, 180)
