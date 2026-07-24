from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


TIMESTAMP = re.compile(
    r"^(\d+)\n"
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\n"
    r"(.+)$",
    re.S,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an SRT file.")
    parser.add_argument("srt", type=Path)
    parser.add_argument("--video", type=Path)
    return parser.parse_args()


def seconds(groups: tuple[str, ...]) -> float:
    return (
        int(groups[0]) * 3600
        + int(groups[1]) * 60
        + int(groups[2])
        + int(groups[3]) / 1000
    )


def video_duration(path: Path | None) -> float | None:
    if path is None:
        return None
    try:
        import av
    except ImportError as exception:
        raise SystemExit("PyAV is required when --video is used.") from exception
    with av.open(str(path)) as container:
        return float(container.duration / av.time_base) if container.duration else None


def main() -> None:
    args = parse_args()
    raw = args.srt.read_bytes()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        text = raw.decode("utf-8").replace("\r\n", "\n")
    except UnicodeDecodeError as exception:
        raise SystemExit(f"Invalid UTF-8: {exception}") from exception
    if "\x00" in text:
        errors.append("NUL byte found")
    if "\ufffd" in text:
        errors.append("Unicode replacement character found")

    cues = []
    for block in [item for item in text.strip().split("\n\n") if item]:
        match = TIMESTAMP.match(block)
        if not match:
            errors.append(f"Invalid SRT block: {block[:80]!r}")
            continue
        groups = match.groups()
        cues.append(
            (
                int(groups[0]),
                seconds(groups[1:5]),
                seconds(groups[5:9]),
                groups[9],
            )
        )

    if not cues:
        errors.append("No subtitle cues")
    else:
        expected = list(range(1, len(cues) + 1))
        if [cue[0] for cue in cues] != expected:
            errors.append("Cue numbers are not consecutive")
        for index, cue in enumerate(cues):
            duration = cue[2] - cue[1]
            if duration <= 0:
                errors.append(f"Cue {cue[0]} has non-positive duration")
            elif duration < 0.35:
                errors.append(f"Cue {cue[0]} is shorter than 0.35 seconds")
            elif duration > 7:
                warnings.append(f"Cue {cue[0]} is longer than 7 seconds")
            if len(cue[3].replace("\n", " ")) > 64:
                warnings.append(f"Cue {cue[0]} is longer than 64 characters")
            if index and cue[1] < cues[index - 1][2] - 0.001:
                errors.append(f"Cue {cue[0]} overlaps cue {cues[index - 1][0]}")

        duration = video_duration(args.video)
        if duration is not None and cues[-1][2] > duration + 0.001:
            errors.append("Last cue exceeds video duration")
    duration = duration if cues and args.video else None
    result = {
        "status": "valid" if not errors else "invalid",
        "srt": str(args.srt.resolve()),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "cues": len(cues),
        "first_start": cues[0][1] if cues else None,
        "last_end": cues[-1][2] if cues else None,
        "video_duration": duration,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
