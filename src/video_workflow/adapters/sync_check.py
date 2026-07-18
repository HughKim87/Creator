"""Sync-check port of the legacy ``tools/synccheck`` slice.

Pure calculations (time parsing, SRT parsing, RMS windowing, subtitle-lag
scoring) are ported without numpy and never touch files or processes. The
audio extraction that legacy piped through ffmpeg lives in a separate
adapter function. Results are structured (scope, status, metrics, evidence,
failure code); exceptions are never converted into string successes, and an
insufficient-data outcome is a distinct status, not a pass.
"""

from __future__ import annotations

import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

SAMPLE_RATE = 16000
HOP_SECONDS = 0.05
LAG_RANGE_SECONDS = 15.0
LAG_STEP_SECONDS = 0.05
MIN_WINDOWS_PER_SIDE = 10

_SRT_TIME = re.compile(r"^(\d+):(\d+):(\d+),(\d+)$")


class SyncCheckError(RuntimeError):
    """Sync check could not run; never reported as success."""


def parse_time(value: str) -> float:
    """Seconds, MM:SS, or HH:MM:SS(.ms) — same grammar as legacy align.py."""
    parts = [float(part) for part in value.strip().split(":")]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"bad time: {value!r}")


def parse_clip(value: str) -> tuple[str, float, float]:
    """``NAME:START-END`` clip specification (legacy grammar)."""
    name, span = value.split(":", 1)
    start, end = span.split("-", 1)
    return name.strip(), parse_time(start), parse_time(end)


def _srt_timestamp_seconds(text: str) -> float:
    match = _SRT_TIME.match(text.strip())
    if match is None:
        raise ValueError(f"bad SRT timestamp: {text!r}")
    hours, minutes, seconds, millis = (int(part) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def parse_srt(text: str) -> list[tuple[float, float, str]]:
    """Parse SRT text into (start, end, joined text) blocks (legacy port)."""
    blocks: list[tuple[float, float, str]] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().split("\n")
        if len(lines) >= 2 and "-->" in lines[1]:
            start_text, end_text = (part.strip() for part in lines[1].split("-->"))
            blocks.append(
                (
                    _srt_timestamp_seconds(start_text),
                    _srt_timestamp_seconds(end_text),
                    " ".join(lines[2:]),
                )
            )
    return blocks


def rms_windows(pcm_s16le: bytes, sample_rate: int = SAMPLE_RATE) -> list[float]:
    """Windowed RMS over mono s16le PCM (pure port of legacy rms_curve)."""
    window = int(sample_rate * HOP_SECONDS)
    total_samples = len(pcm_s16le) // 2
    windows = total_samples // window
    values: list[float] = []
    for index in range(windows):
        offset = index * window * 2
        accumulator = 0.0
        for sample_index in range(window):
            position = offset + sample_index * 2
            sample = int.from_bytes(pcm_s16le[position : position + 2], "little", signed=True)
            normalized = sample / 32768
            accumulator += normalized * normalized
        values.append(math.sqrt(accumulator / window))
    return values


@dataclass(frozen=True, slots=True)
class LagScore:
    lag_seconds: float
    score: float


@dataclass(frozen=True, slots=True)
class SyncCheckResult:
    """Structured result; ``status`` is one of ok/insufficient_data."""

    scope: str
    status: str
    clip_name: str
    best_lag_seconds: float | None
    best_score: float | None
    zero_lag_score: float | None
    top_lags: tuple[LagScore, ...]
    failure_code: str | None
    evidence: str


def _subtitle_mask(
    blocks: list[tuple[float, float, str]],
    window_start: float,
    window_count: int,
    lag: float,
) -> list[bool]:
    mask = [False] * window_count
    horizon = window_start + window_count * HOP_SECONDS + 30
    for start, end, _text in blocks:
        if end < window_start - 30 or start > horizon:
            continue
        for index in range(window_count):
            t = window_start + index * HOP_SECONDS - lag
            if start <= t <= end:
                mask[index] = True
    return mask


def score_lags(
    energy: list[float],
    blocks: list[tuple[float, float, str]],
    window_start: float,
) -> list[LagScore]:
    """Score candidate lags exactly like legacy align.analyze (pure)."""
    log_energy = [math.log10(value + 1e-5) for value in energy]
    scores: list[LagScore] = []
    steps = int(round((2 * LAG_RANGE_SECONDS) / LAG_STEP_SECONDS)) + 1
    for step in range(steps):
        lag = -LAG_RANGE_SECONDS + step * LAG_STEP_SECONDS
        mask = _subtitle_mask(blocks, window_start, len(log_energy), lag)
        inside = [log_energy[i] for i, flag in enumerate(mask) if flag]
        outside = [log_energy[i] for i, flag in enumerate(mask) if not flag]
        if len(inside) < MIN_WINDOWS_PER_SIDE or len(outside) < MIN_WINDOWS_PER_SIDE:
            continue
        score = sum(inside) / len(inside) - sum(outside) / len(outside)
        scores.append(LagScore(lag_seconds=round(lag, 2), score=score))
    return scores


def analyze_clip(
    energy: list[float],
    blocks: list[tuple[float, float, str]],
    clip_name: str,
    window_start: float,
    evidence: str,
) -> SyncCheckResult:
    """Pure analysis of one clip. Insufficient data is its own status."""
    if not energy:
        return SyncCheckResult(
            scope="subtitle_audio_alignment",
            status="insufficient_data",
            clip_name=clip_name,
            best_lag_seconds=None,
            best_score=None,
            zero_lag_score=None,
            top_lags=(),
            failure_code="no_audio_samples",
            evidence=evidence,
        )
    scores = score_lags(energy, blocks, window_start)
    if not scores:
        return SyncCheckResult(
            scope="subtitle_audio_alignment",
            status="insufficient_data",
            clip_name=clip_name,
            best_lag_seconds=None,
            best_score=None,
            zero_lag_score=None,
            top_lags=(),
            failure_code="insufficient_overlap",
            evidence=evidence,
        )
    best = max(scores, key=lambda item: item.score)
    zero = min(scores, key=lambda item: abs(item.lag_seconds))
    top = tuple(sorted(scores, key=lambda item: -item.score)[:5])
    return SyncCheckResult(
        scope="subtitle_audio_alignment",
        status="ok",
        clip_name=clip_name,
        best_lag_seconds=best.lag_seconds,
        best_score=best.score,
        zero_lag_score=zero.score,
        top_lags=top,
        failure_code=None,
        evidence=evidence,
    )


def extract_pcm(
    video: Path,
    start_seconds: float,
    duration_seconds: float,
    ffmpeg: str | None = None,
    timeout: float = 300.0,
) -> bytes:
    """Adapter: extract mono s16le PCM via ffmpeg (external execution)."""
    executable = ffmpeg or shutil.which("ffmpeg")
    if executable is None:
        raise SyncCheckError("ffmpeg executable not found; sync check cannot run")
    if not video.is_file():
        raise SyncCheckError(f"video not found: {video.name}")
    completed = subprocess.run(
        [
            executable,
            "-v",
            "error",
            "-ss",
            str(max(start_seconds, 0)),
            "-t",
            str(duration_seconds),
            "-i",
            str(video),
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-f",
            "s16le",
            "-",
        ],
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise SyncCheckError(
            f"ffmpeg failed (exit {completed.returncode}): "
            f"{completed.stderr.decode(errors='replace').strip()[:200]}"
        )
    return completed.stdout
