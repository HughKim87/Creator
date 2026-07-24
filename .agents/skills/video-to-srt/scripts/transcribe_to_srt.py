from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe video audio and create a refined SRT file."
    )
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--raw-json", type=Path)
    parser.add_argument("--model", default="large-v3-turbo")
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--language", default="ko")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--compute-type")
    parser.add_argument("--cpu-threads", type=int, default=8)
    parser.add_argument("--initial-prompt", default="")
    parser.add_argument("--glossary", type=Path)
    parser.add_argument("--postprocess-only", action="store_true")
    return parser.parse_args()


def load_glossary(path: Path | None) -> tuple[list[str], list[tuple[str, str]]]:
    if path is None:
        return [], []
    data = json.loads(path.read_text(encoding="utf-8"))
    terms = [str(item).strip() for item in data.get("terms", []) if str(item).strip()]
    replacements = []
    for item in data.get("replacements", []):
        before = str(item.get("from", ""))
        after = str(item.get("to", ""))
        if before:
            replacements.append((before, after))
    return terms, replacements


def correct(text: str, replacements: list[tuple[str, str]]) -> str:
    result = " ".join(text.split()).strip()
    for before, after in replacements:
        result = result.replace(before, after)
    return result


def stamp(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"


def two_lines(text: str, limit: int = 28) -> str:
    if len(text) <= limit:
        return text
    words = text.split()
    best: tuple[float, str, str] | None = None
    for index in range(1, len(words)):
        left = " ".join(words[:index])
        right = " ".join(words[index:])
        score = max(len(left), len(right)) + abs(len(left) - len(right)) * 0.15
        if best is None or score < best[0]:
            best = (score, left, right)
    if best:
        return best[1] + "\n" + best[2]
    return text


def split_text(text: str, max_chars: int = 52) -> list[str]:
    sentences = [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", text)
        if item.strip()
    ]
    parts: list[str] = []
    for sentence in sentences:
        if len(sentence) <= max_chars:
            parts.append(sentence)
            continue
        clauses = [
            item.strip()
            for item in re.split(r"(?<=[,;:])\s+", sentence)
            if item.strip()
        ]
        if len(clauses) == 1:
            words = sentence.split()
            current: list[str] = []
            for word in words:
                candidate = " ".join(current + [word])
                if current and len(candidate) > max_chars:
                    parts.append(" ".join(current))
                    current = []
                current.append(word)
            if current:
                parts.append(" ".join(current))
            continue
        current = ""
        for clause in clauses:
            candidate = (current + " " + clause).strip()
            if current and len(candidate) > max_chars:
                parts.append(current)
                current = clause
            else:
                current = candidate
        if current:
            parts.append(current)
    return parts or [text]


def distribute(
    text: str,
    start: float,
    end: float,
) -> list[tuple[float, float, str]]:
    parts = split_text(text)
    if len(parts) == 1:
        return [(start, end, parts[0])]
    weights = [max(1, len(part)) for part in parts]
    total_weight = sum(weights)
    duration = max(0.5, end - start)
    cues = []
    cursor = start
    for index, (part, weight) in enumerate(zip(parts, weights)):
        part_end = end if index == len(parts) - 1 else cursor + duration * weight / total_weight
        cues.append((cursor, max(cursor + 0.35, part_end), part))
        cursor = part_end
    return cues


def normalized_length(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def transcribe(
    args: argparse.Namespace,
    initial_prompt: str,
) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exception:
        raise SystemExit(
            "faster-whisper is required. Install it only after user approval."
        ) from exception

    compute_type = args.compute_type or (
        "int8_float16" if args.device == "cuda" else "int8"
    )

    def run(device: str, selected_compute_type: str) -> dict[str, Any]:
        print(
            json.dumps(
                {
                    "stage": "model_loading",
                    "model": args.model,
                    "device": device,
                    "compute_type": selected_compute_type,
                }
            ),
            flush=True,
        )
        model = WhisperModel(
            args.model,
            device=device,
            compute_type=selected_compute_type,
            cpu_threads=args.cpu_threads,
            download_root=str(args.model_dir) if args.model_dir else None,
        )
        iterator, info = model.transcribe(
            str(args.video),
            language=args.language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 400},
            word_timestamps=True,
            condition_on_previous_text=True,
            initial_prompt=initial_prompt or None,
            temperature=0.0,
        )
        segments = []
        for index, segment in enumerate(iterator, start=1):
            segments.append(
                {
                    "id": index,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "words": [
                        {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                            "probability": word.probability,
                        }
                        for word in (segment.words or [])
                    ],
                }
            )
            if index % 25 == 0:
                print(
                    json.dumps(
                        {
                            "stage": "progress",
                            "segments": index,
                            "audio_time": round(segment.end, 1),
                        }
                    ),
                    flush=True,
                )
        return {
            "source": args.video.name,
            "model": args.model,
            "device": f"{device}/{selected_compute_type}",
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": segments,
        }

    try:
        return run(args.device, compute_type)
    except RuntimeError as exception:
        if args.device != "cuda":
            raise
        print(
            json.dumps(
                {
                    "stage": "cuda_failed",
                    "error": str(exception),
                    "fallback": "cpu/int8",
                }
            ),
            file=sys.stderr,
            flush=True,
        )
        return run("cpu", "int8")


def refine(
    data: dict[str, Any],
    replacements: list[tuple[str, str]],
) -> list[tuple[float, float, str]]:
    segments = data["segments"]
    cues: list[tuple[float, float, str]] = []
    for index, segment in enumerate(segments):
        text = correct(segment["text"], replacements)
        words = [
            word
            for word in segment.get("words", [])
            if word.get("start") is not None
            and word.get("end") is not None
            and word.get("word", "").strip()
        ]
        word_text = correct("".join(word["word"] for word in words), replacements)
        coverage = (
            normalized_length(word_text) / max(1, normalized_length(text))
            if words
            else 0.0
        )
        if coverage < 0.72:
            effective_end = float(segment["end"])
            if index + 1 < len(segments):
                next_start = float(segments[index + 1]["start"])
                if next_start - effective_end > 1 and next_start - float(segment["start"]) <= 15:
                    effective_end = next_start - 0.12
            cues.extend(distribute(text, float(segment["start"]), effective_end))
            continue

        current: list[dict[str, Any]] = []
        for word in words:
            candidate = correct(
                "".join(item["word"] for item in current + [word]),
                replacements,
            )
            duration = (
                float(word["end"]) - float(current[0]["start"])
                if current
                else float(word["end"]) - float(word["start"])
            )
            if current and (len(candidate) > 52 or duration > 6.5):
                cues.append(
                    (
                        float(current[0]["start"]),
                        float(current[-1]["end"]),
                        correct("".join(item["word"] for item in current), replacements),
                    )
                )
                current = []
            current.append(word)
            current_text = correct(
                "".join(item["word"] for item in current),
                replacements,
            )
            current_duration = float(current[-1]["end"]) - float(current[0]["start"])
            if (
                current_duration >= 1.4
                and len(current_text) >= 10
                and current_text.endswith((".", "?", "!", "。", "？", "！", "…"))
            ):
                cues.append(
                    (
                        float(current[0]["start"]),
                        float(current[-1]["end"]),
                        current_text,
                    )
                )
                current = []
        if current:
            cues.append(
                (
                    float(current[0]["start"]),
                    float(current[-1]["end"]),
                    correct("".join(item["word"] for item in current), replacements),
                )
            )

    merged: list[tuple[float, float, str]] = []
    for start, end, text in cues:
        text = correct(text, replacements)
        if not text:
            continue
        if merged:
            prior_start, prior_end, prior_text = merged[-1]
            same = re.sub(r"\W+", "", prior_text) == re.sub(r"\W+", "", text)
            if (same or prior_text.endswith(text)) and start - prior_end < 1:
                continue
            if end - start < 0.7 and start - prior_end < 1:
                merged[-1] = (
                    prior_start,
                    max(prior_end, end),
                    correct(prior_text + " " + text, replacements),
                )
                continue
        merged.append((start, max(start + 0.35, end), text))

    result: list[tuple[float, float, str]] = []
    for start, end, text in merged:
        if result and start < result[-1][1]:
            prior_start, prior_end, prior_text = result[-1]
            if start > prior_start + 0.1:
                result[-1] = (prior_start, start, prior_text)
            else:
                result[-1] = (
                    prior_start,
                    max(prior_end, end),
                    correct(prior_text + " " + text, replacements),
                )
                continue
        result.append((start, end, text))
    return result


def main() -> None:
    args = parse_args()
    args.video = args.video.resolve()
    if not args.video.is_file() or args.video.stat().st_size == 0:
        raise SystemExit(f"Video is missing or empty: {args.video}")

    output = (args.output or args.video.with_suffix(".srt")).resolve()
    raw_json = (
        args.raw_json or output.with_name(output.stem + ".transcript.json")
    ).resolve()
    terms, replacements = load_glossary(args.glossary)
    initial_prompt = ", ".join(
        item for item in [args.initial_prompt.strip(), *terms] if item
    )
    started = time.time()

    if args.postprocess_only:
        if not raw_json.is_file():
            raise SystemExit(f"Raw transcript JSON is missing: {raw_json}")
        data = json.loads(raw_json.read_text(encoding="utf-8"))
    else:
        data = transcribe(args, initial_prompt)
        raw_json.parent.mkdir(parents=True, exist_ok=True)
        raw_json.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    cues = refine(data, replacements)
    if not cues:
        raise SystemExit("No subtitle cues were produced.")
    blocks = [
        f"{index}\n{stamp(start)} --> {stamp(end)}\n{two_lines(text)}"
        for index, (start, end, text) in enumerate(cues, start=1)
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "stage": "complete",
                "device": data.get("device"),
                "elapsed_seconds": round(time.time() - started, 1),
                "segments": len(data["segments"]),
                "cues": len(cues),
                "first_start": cues[0][0],
                "last_end": cues[-1][1],
                "srt": str(output),
                "raw_json": str(raw_json),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
