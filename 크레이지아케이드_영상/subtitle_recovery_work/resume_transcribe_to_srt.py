import os
import re
import sys
from pathlib import Path


TIME_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})"
)


def parse_time(value: str) -> float:
    match = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", value)
    if not match:
        raise ValueError(value)
    h, m, s, ms = map(int, match.groups())
    return h * 3600 + m * 60 + s + ms / 1000


def srt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    millis = int(round(seconds * 1000))
    hours = millis // 3_600_000
    millis %= 3_600_000
    minutes = millis // 60_000
    millis %= 60_000
    secs = millis // 1000
    millis %= 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def read_complete_cues(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\n\s*\n", text.strip())
    cues = []
    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or not lines[0].isdigit() or not TIME_RE.match(lines[1]):
            continue
        match = TIME_RE.match(lines[1])
        if not match:
            continue
        start = parse_time(lines[1].split("-->")[0].strip())
        end = parse_time(lines[1].split("-->")[1].strip())
        body = " ".join(line.strip() for line in lines[2:] if line.strip())
        if body:
            cues.append((start, end, body))
    return cues


def main() -> int:
    if len(sys.argv) != 5:
        print("usage: resume_transcribe_to_srt.py <video> <partial_srt> <existing_text> <output_srt>", file=sys.stderr)
        return 2

    video = Path(sys.argv[1])
    partial = Path(sys.argv[2])
    existing_text = Path(sys.argv[3])
    output = Path(sys.argv[4])

    deps = Path(__file__).resolve().parent / "pydeps2"
    sys.path.insert(0, str(deps))

    from faster_whisper import WhisperModel

    cues = read_complete_cues(partial)
    resume_start = max(cues[-1][1] - 0.5, 0) if cues else 0
    next_index = len(cues) + 1
    print(f"keeping {len(cues)} complete cues; resuming from {srt_time(resume_start)}", flush=True)

    prompt = ""
    if existing_text.exists():
        raw = existing_text.read_text(encoding="utf-8", errors="ignore")
        prompt = " ".join(raw.split()[:160])

    model_name = os.environ.get("WHISPER_MODEL", "small")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as f:
        for index, (start, end, body) in enumerate(cues, 1):
            f.write(f"{index}\n{srt_time(start)} --> {srt_time(end)}\n{body}\n\n")

        segments, _ = model.transcribe(
            str(video),
            language="ko",
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            initial_prompt=prompt or None,
            clip_timestamps=f"{resume_start}",
        )

        for segment in segments:
            start = segment.start
            end = segment.end
            if start < resume_start - 60:
                start += resume_start
                end += resume_start
            if end <= resume_start:
                continue
            text = " ".join(segment.text.strip().split())
            if not text:
                continue
            f.write(f"{next_index}\n")
            f.write(f"{srt_time(start)} --> {srt_time(end)}\n")
            f.write(f"{text}\n\n")
            if next_index % 25 == 0:
                print(f"written {next_index} cues, last={srt_time(end)}", flush=True)
            next_index += 1

    print(f"done: {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
