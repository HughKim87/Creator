import os
import sys
from pathlib import Path


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


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: transcribe_to_srt.py <video> <existing_text> <output_srt>", file=sys.stderr)
        return 2

    video = Path(sys.argv[1])
    existing_text = Path(sys.argv[2])
    output = Path(sys.argv[3])

    deps = Path(__file__).resolve().parent / "pydeps"
    sys.path.insert(0, str(deps))

    from faster_whisper import WhisperModel

    prompt = ""
    if existing_text.exists():
        text = existing_text.read_text(encoding="utf-8", errors="ignore")
        prompt = " ".join(text.split()[:160])

    model_name = os.environ.get("WHISPER_MODEL", "small")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")

    segments, info = model.transcribe(
        str(video),
        language="ko",
        task="transcribe",
        beam_size=5,
        vad_filter=True,
        initial_prompt=prompt or None,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as f:
        for index, segment in enumerate(segments, 1):
            text = " ".join(segment.text.strip().split())
            if not text:
                continue
            f.write(f"{index}\n")
            f.write(f"{srt_time(segment.start)} --> {srt_time(segment.end)}\n")
            f.write(f"{text}\n\n")
            if index % 25 == 0:
                print(f"written {index} segments, last={srt_time(segment.end)}", flush=True)

    print(f"done: {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
