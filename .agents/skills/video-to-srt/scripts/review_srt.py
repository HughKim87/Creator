#!/usr/bin/env python3
"""Prepare and record a full-caption semantic and spelling review."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


NON_WORD = re.compile(r"[^\w가-힣]+", re.UNICODE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("srt", type=Path)
    parser.add_argument("--raw-json", required=True, type=Path)
    parser.add_argument("--glossary", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--low-confidence-threshold", type=float, default=0.85)
    parser.add_argument("--confirm-full-read", action="store_true")
    return parser.parse_args()


def normalized(value: str) -> str:
    return NON_WORD.sub("", value).lower()


def build_review(
    srt: Path,
    raw_json: Path,
    glossary: Path,
    *,
    low_confidence_threshold: float,
    confirm_full_read: bool,
) -> dict[str, Any]:
    if not 0 <= low_confidence_threshold <= 1:
        raise ValueError("low_confidence_threshold must be between 0 and 1")
    if not srt.is_file() or not raw_json.is_file() or not glossary.is_file():
        raise FileNotFoundError("SRT, raw transcript, and glossary must all exist")

    srt_bytes = srt.read_bytes()
    srt_text = srt_bytes.decode("utf-8-sig")
    compact_srt = normalized(srt_text)
    transcript = json.loads(raw_json.read_text(encoding="utf-8"))
    glossary_data = json.loads(glossary.read_text(encoding="utf-8"))

    replacement_source_hits = []
    for item in glossary_data.get("replacements", []):
        before = str(item.get("from", "")).strip()
        after = str(item.get("to", "")).strip()
        if before and normalized(before) in compact_srt:
            replacement_source_hits.append({"from": before, "to": after})

    low_confidence_words = []
    for segment in transcript.get("segments", []):
        for word in segment.get("words", []):
            token = str(word.get("word", "")).strip()
            probability = word.get("probability")
            if not token or not isinstance(probability, (int, float)):
                continue
            if probability < low_confidence_threshold:
                low_confidence_words.append(
                    {
                        "segment_id": segment.get("id"),
                        "start": word.get("start"),
                        "end": word.get("end"),
                        "word": token,
                        "probability": round(float(probability), 4),
                        "present_in_final_srt": normalized(token) in compact_srt,
                    }
                )

    if replacement_source_hits:
        status = "invalid"
    elif confirm_full_read:
        status = "reviewed"
    else:
        status = "needs_manual_review"

    return {
        "schema_version": "caption-review-v1",
        "status": status,
        "srt": str(srt.resolve()),
        "srt_sha256": hashlib.sha256(srt_bytes).hexdigest(),
        "raw_json": str(raw_json.resolve()),
        "glossary": str(glossary.resolve()),
        "low_confidence_threshold": low_confidence_threshold,
        "low_confidence_words": low_confidence_words,
        "replacement_source_hits": replacement_source_hits,
        "manual_review": {
            "full_srt_reviewed": confirm_full_read,
            "scope": "all_cues" if confirm_full_read else "pending",
        },
    }


def main() -> int:
    args = parse_args()
    try:
        result = build_review(
            args.srt.resolve(),
            args.raw_json.resolve(),
            args.glossary.resolve(),
            low_confidence_threshold=args.low_confidence_threshold,
            confirm_full_read=args.confirm_full_read,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
