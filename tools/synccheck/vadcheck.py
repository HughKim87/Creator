#!/usr/bin/env python3
"""Check whether selected cut boundaries split speech.

Usage:
  python tools/synccheck/vadcheck.py VIDEO SRT --clip "NAME:START-END"
"""
import argparse
import subprocess
from pathlib import Path

from srt_slice import parse


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


def parse_clip(value):
    name, span = value.split(":", 1)
    start, end = span.split("-", 1)
    return name.strip(), parse_time(start), parse_time(end)


def speech_segments(video, lo, dur, ffmpeg, aggressiveness=3):
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
    return [seg for seg in out if seg[1] - seg[0] >= 0.2]


def report(video, blocks, name, clip_lo, clip_hi, ffmpeg):
    print(f"== {name} ({clip_lo:.2f}~{clip_hi:.2f}) ==")
    lo = max(clip_lo - 6, 0)
    dur = (clip_hi - clip_lo) + 12
    segs = speech_segments(video, lo, dur, ffmpeg)
    print(" VAD speech:", "; ".join(f"{a:.1f}-{b:.1f}" for a, b in segs) or "none")

    for start, end, text in blocks:
        if end < clip_lo - 6 or start > clip_hi + 6:
            continue
        near = [seg for seg in segs if abs(seg[0] - start) < 3]
        delta = f"{min(near, key=lambda seg: abs(seg[0] - start))[0] - start:+.2f}s" if near else "none<3s"
        print(f"  srt[{start:8.2f}-{end:8.2f}] vs speech_start {delta} | {text[:50]}")

    for edge, label in [(clip_lo, "START"), (clip_hi, "END")]:
        cross = [seg for seg in segs if seg[0] < edge < seg[1]]
        if cross:
            seg = cross[0]
            print(f"  WARN {label} {edge:.2f}s splits speech ({seg[0]:.1f}~{seg[1]:.1f})")
        else:
            print(f"  OK {label} {edge:.2f}s does not split speech")


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
        report(args.video, blocks, *parse_clip(clip), args.ffmpeg)


if __name__ == "__main__":
    main()
