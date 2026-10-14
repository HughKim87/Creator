"""Bound reference length and align SRT words to the selected audio window."""
import json
import re
import subprocess
from pathlib import Path


def read_srt_file(path):
    source = Path(path)
    if source.suffix.lower() != ".srt":
        raise ValueError(".srt 자막 파일을 선택하세요.")
    if source.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("자막 파일은 2MB 이하로 넣어주세요.")
    raw = source.read_bytes()
    for encoding in ("utf-8-sig", "cp949"):
        try:
            text = raw.decode(encoding).replace("\r\n", "\n").replace("\r", "\n").strip()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("자막 인코딩을 읽을 수 없습니다. UTF-8로 저장해주세요.")
    if not text or not any(TIME_LINE.match(line.strip()) for line in text.splitlines()):
        raise ValueError("유효한 SRT 타임코드가 없습니다. 자막 파일을 확인하세요.")
    return text

TIME_LINE = re.compile(r"^(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})")


def seconds(timestamp):
    hours, minutes, rest = timestamp.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(rest)


def select_reference(duration, transcript):
    if duration < 20:
        raise ValueError("목소리 등록에는 최소 20초 녹음이 필요합니다.")
    cues = []
    for block in re.split(r"\n\s*\n", transcript.replace("\r", "").strip()):
        lines = block.splitlines()
        for index, line in enumerate(lines):
            match = TIME_LINE.match(line.strip())
            if match:
                text = " ".join(lines[index + 1:]).strip()
                start, end = map(seconds, match.groups())
                if not text or end <= start or start < 0 or end > duration + 1:
                    raise ValueError("SRT 시간과 녹음 길이가 맞지 않습니다. 같은 녹음의 자막을 사용하세요.")
                if cues and start < cues[-1][0]:
                    raise ValueError("SRT 자막의 시간 순서를 확인하세요.")
                cues.append((start, end, text))
                break
    if not cues:
        if "-->" in transcript:
            raise ValueError("SRT 형식을 확인하세요. 또는 짧은 녹음과 해당 발화문을 입력하세요.")
        if duration > 60:
            raise ValueError("60초보다 긴 녹음에는 같은 녹음의 SRT를 넣어주세요. 20~60초 녹음은 해당 구간의 발화문을 입력하세요.")
        return 0.0, duration, transcript.strip()
    start = 0.0
    selected = []
    for cue in cues:
        if cue[1] > min(duration + 1, 60):
            break
        selected.append(cue)
    if not selected:
        raise ValueError("60초 이내에 끝나는 SRT 문장이 필요합니다. 녹음과 자막 구간을 확인하세요.")
    end = duration if duration <= 60 else selected[-1][1]
    if end < 20:
        raise ValueError("SRT로 선택할 수 있는 구간이 20초보다 짧습니다. 20~60초 구간과 일치하는 자막을 사용하세요.")
    return start, end, " ".join(c[2] for c in selected)


def prepare_reference(path, transcript):
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "json", str(path)], capture_output=True, check=True, timeout=15)
    duration = float(json.loads(probe.stdout)["format"]["duration"])
    if duration <= 0:
        raise ValueError("녹음이 비어 있습니다.")
    start, end, text = select_reference(duration, transcript)
    decoded = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start),
                              "-i", str(path), "-t", str(end - start), "-ac", "1", "-ar", "24000",
                              "-f", "f32le", "pipe:1"], capture_output=True, check=True, timeout=20)
    import numpy as np
    wave = np.frombuffer(decoded.stdout, dtype="<f4").copy()
    if wave.size == 0 or not np.isfinite(wave).all():
        raise ValueError("녹음을 읽을 수 없습니다.")
    return (wave, 24000), text, f"참고 녹음 {start:.2f}~{end:.2f}초 사용"
