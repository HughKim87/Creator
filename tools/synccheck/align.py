#!/usr/bin/env python3
"""Estimate subtitle/audio lag for selected clips.

Usage:
  python tools/synccheck/align.py VIDEO SRT --clip "NAME:START-END"

Times may be seconds, MM:SS, or HH:MM:SS(.ms). The script reads the supplied
video/SRT paths only; no project-specific source file is hard-coded.
"""
import argparse
import subprocess
from pathlib import Path

import numpy as np

from srt_slice import parse


SR = 16000
HOP = 0.05


def parse_time(value):
    parts = [float(p) for p in value.strip().split(":")]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"Bad time: {value}")


def parse_clip(value):
    name, span = value.split(":", 1)
    start, end = span.split("-", 1)
    return name.strip(), parse_time(start), parse_time(end)


def rms_curve(video, lo, dur, ffmpeg):
    cmd = [
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
    ]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    n = int(SR * HOP)
    m = len(x) // n
    if m == 0:
        return np.array([], dtype=np.float32)
    return np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(axis=1))


def subtitle_mask(blocks, lo, m_len, lag):
    t = lo + np.arange(m_len) * HOP - lag
    mask = np.zeros(m_len, bool)
    for start, end, _ in blocks:
        if end < lo - 30 or start > lo + m_len * HOP + 30:
            continue
        mask |= (t >= start) & (t <= end)
    return mask


def analyze(video, blocks, name, clip_lo, clip_hi, ffmpeg):
    lo = max(clip_lo - 20, 0)
    dur = (clip_hi - clip_lo) + 40
    energy = rms_curve(video, lo, dur, ffmpeg)
    if len(energy) == 0:
        print(f"{name}: no audio samples")
        return

    log_energy = np.log10(energy + 1e-5)
    best = None
    scores = []
    for lag in np.arange(-15, 15.01, 0.05):
        mask = subtitle_mask(blocks, lo, len(log_energy), lag)
        if mask.sum() < 10 or (~mask).sum() < 10:
            continue
        score = log_energy[mask].mean() - log_energy[~mask].mean()
        scores.append((lag, score))
        if best is None or score > best[1]:
            best = (lag, score)

    if not best:
        print(f"{name}: insufficient subtitle/audio overlap")
        return

    zero_score = min(scores, key=lambda item: abs(item[0]))[1]
    print(
        f"{name}: best_lag={best[0]:+.2f}s "
        f"(score {best[1]:.3f}) | lag0 score {zero_score:.3f}"
    )
    top = sorted(scores, key=lambda item: -item[1])[:5]
    print("   top lags:", ", ".join(f"{lag:+.2f}({score:.3f})" for lag, score in top))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("srt", type=Path)
    parser.add_argument("--clip", action="append", required=True, help="NAME:START-END")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()

    if not args.video.exists():
        raise SystemExit(f"Video not found: {args.video}")
    if not args.srt.exists():
        raise SystemExit(f"SRT not found: {args.srt}")

    blocks = parse(str(args.srt))
    for clip in args.clip:
        analyze(args.video, blocks, *parse_clip(clip), args.ffmpeg)


if __name__ == "__main__":
    main()
