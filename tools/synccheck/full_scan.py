#!/usr/bin/env python3
"""Scan a cutlist for speech-boundary risks.

Usage:
  python tools/synccheck/full_scan.py VIDEO CUTLIST.csv

The CSV must contain start/end/label columns. Accepted Korean headers include
시작, 끝, 라벨. The script prints suggestions only and does not overwrite files.
"""
import argparse
import csv
import subprocess
from pathlib import Path

SR = 16000
FRAME = 0.03


def parse_time(value):
    parts = [float(p) for p in value.strip().split(":")]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"Bad time: {value}")


def format_time(seconds):
    seconds = round(max(seconds, 0), 1)
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds - h * 3600 - m * 60
    if abs(s - round(s)) < 1e-9:
        return f"{h:02d}:{m:02d}:{int(round(s)):02d}"
    return f"{h:02d}:{m:02d}:{s:04.1f}"


def pick(row, names):
    lowered = {key.strip().lower(): value for key, value in row.items()}
    for name in names:
        if name in row:
            return row[name]
        if name.lower() in lowered:
            return lowered[name.lower()]
    raise KeyError(f"Missing column. Expected one of: {', '.join(names)}")


def read_cutlist(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    cuts = []
    for i, row in enumerate(rows, 1):
        start = parse_time(pick(row, ["start", "시작"]))
        end = parse_time(pick(row, ["end", "끝"]))
        label = pick(row, ["label", "라벨", "name", "구간명"])
        if not start < end:
            raise ValueError(f"Invalid cut at row {i}: {start} >= {end}")
        cuts.append((start, end, label))
    return cuts


def speech_segments(video, lo, dur, ffmpeg, aggressiveness):
    try:
        import webrtcvad
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing dependency: install webrtcvad or webrtcvad-wheels") from exc

    raw = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-ss",
            str(max(lo, 0)),
            "-t",
            str(dur),
            "-i",
            str(video),
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(SR),
            "-f",
            "s16le",
            "-",
        ],
        capture_output=True,
        check=True,
    ).stdout
    vad = webrtcvad.Vad(aggressiveness)
    frame_bytes = int(SR * FRAME) * 2
    flags = [
        vad.is_speech(raw[i : i + frame_bytes], SR)
        for i in range(0, len(raw) - frame_bytes, frame_bytes)
    ]
    out = []
    cur = None
    gap = 0
    for i, flag in enumerate(flags):
        t = max(lo, 0) + i * FRAME
        if flag:
            if cur is None:
                cur = [t, t + FRAME]
            else:
                cur[1] = t + FRAME
            gap = 0
        elif cur:
            gap += 1
            if gap > 10:
                out.append(cur)
                cur = None
    if cur:
        out.append(cur)
    return [seg for seg in out if seg[1] - seg[0] >= 0.25]


def scan(video, cuts, ffmpeg, aggressiveness):
    print("### Boundary scan")
    for idx, (start, end, label) in enumerate(cuts, 1):
        messages = []
        start_segments = speech_segments(video, max(start - 5, 0), 10, ffmpeg, aggressiveness)
        end_segments = speech_segments(video, max(end - 5, 0), 10, ffmpeg, aggressiveness)

        crossing_start = [seg for seg in start_segments if seg[0] < start < seg[1]]
        if crossing_start:
            seg = crossing_start[0]
            if start - seg[0] <= 2.0:
                messages.append(
                    f"START splits speech by {start - seg[0]:.2f}s -> consider {format_time(max(seg[0] - 0.4, 0))}"
                )
            else:
                messages.append(f"START splits long speech by {start - seg[0]:.2f}s -> manual check")
        else:
            next_speech = [seg for seg in start_segments if seg[0] >= start]
            if next_speech and next_speech[0][0] - start > 2.5:
                messages.append(f"START has {next_speech[0][0] - start:.1f}s idle before speech")

        crossing_end = [seg for seg in end_segments if seg[0] < end < seg[1]]
        if crossing_end:
            seg = crossing_end[0]
            if seg[1] - end <= 2.5:
                messages.append(
                    f"END splits speech with {seg[1] - end:.2f}s remaining -> consider {format_time(seg[1] + 0.4)}"
                )
            else:
                messages.append(f"END splits long speech with {seg[1] - end:.2f}s remaining -> manual check")
        else:
            next_speech = [seg for seg in end_segments if end - 0.1 <= seg[0] <= end + 0.35]
            if next_speech:
                messages.append(
                    f"END is {next_speech[0][0] - end:+.2f}s before new speech -> consider {format_time(next_speech[0][0] - 0.15)}"
                )

        if messages:
            print(f"[{idx:02d}] {label} ({format_time(start)}~{format_time(end)})")
            for message in messages:
                print(f"      {message}")

    print("\n### Adjacent gaps")
    for (start_a, end_a, label_a), (start_b, _end_b, label_b) in zip(cuts, cuts[1:]):
        gap = start_b - end_a
        if 0 < gap <= 3:
            print(f"  {label_a} -> {label_b}: gap {gap:.1f}s")
        elif abs(gap) < 0.01:
            print(f"  {label_a} -> {label_b}: shared boundary")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("cutlist", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--aggressiveness", type=int, default=3, choices=[0, 1, 2, 3])
    args = parser.parse_args()

    if not args.video.exists():
        raise SystemExit(f"Video not found: {args.video}")
    if not args.cutlist.exists():
        raise SystemExit(f"Cutlist not found: {args.cutlist}")

    scan(args.video, read_cutlist(args.cutlist), args.ffmpeg, args.aggressiveness)


if __name__ == "__main__":
    main()
