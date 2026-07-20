"""MediaProbe port and FFprobe adapter.

The port is frozen first (stage 04): ``source_registration`` and the XML
builder depend only on ``MediaProbe``/``MediaInfo``. Unlike the legacy tool,
a missing or failing ffprobe is a structured failure, never a silent
default (fail-closed; recorded as an intentional semantic change from the
legacy ``read_media_info`` fallback).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Protocol


class MediaProbeError(RuntimeError):
    """Probing failed; callers must not continue with guessed metadata."""


@dataclass(frozen=True, slots=True)
class MediaInfo:
    """Media metadata used for frame math and XML generation."""

    duration: float
    width: int
    height: int
    fps: Fraction
    sample_rate: int
    channels: int

    @property
    def timebase(self) -> int:
        return max(1, int(round(float(self.fps))))

    @property
    def ntsc(self) -> bool:
        return self.fps.denominator == 1001

    def __post_init__(self) -> None:
        if self.duration <= 0:
            raise MediaProbeError("media duration must be positive")
        if self.fps <= 0:
            raise MediaProbeError("media fps must be positive")
        if self.channels < 1:
            raise MediaProbeError("media channels must be >= 1")


class MediaProbe(Protocol):
    """Read-only media metadata probe."""

    def probe(self, path: Path) -> MediaInfo: ...


@dataclass(frozen=True, slots=True)
class StaticMediaProbe:
    """Deterministic probe for tests and known-media flows."""

    info: MediaInfo

    def probe(self, path: Path) -> MediaInfo:
        if not path.is_file():
            raise MediaProbeError(f"source file not found: {path.name}")
        return self.info


def _parse_fraction(value: object, field: str) -> Fraction:
    if not isinstance(value, str) or not value or value == "0/0":
        raise MediaProbeError(f"ffprobe returned no usable {field}")
    try:
        parsed = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise MediaProbeError(f"ffprobe returned invalid {field}: {value}") from exc
    if parsed <= 0:
        raise MediaProbeError(f"ffprobe returned non-positive {field}: {value}")
    return parsed


@dataclass(frozen=True, slots=True)
class FfprobeMediaProbe:
    """Probe via the ffprobe executable (external process wrapped here only)."""

    executable: str | None = None
    timeout: float = 60.0

    def probe(self, path: Path) -> MediaInfo:
        if not path.is_file():
            raise MediaProbeError(f"source file not found: {path.name}")
        ffprobe = self.executable or shutil.which("ffprobe")
        if ffprobe is None:
            raise MediaProbeError(
                "ffprobe executable not found; media probing is required and "
                "is never skipped as success"
            )
        completed = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-show_entries",
                "stream=index,codec_type,width,height,r_frame_rate,"
                "avg_frame_rate,sample_rate,channels",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout,
            check=False,
        )
        if completed.returncode != 0:
            raise MediaProbeError(
                f"ffprobe failed (exit {completed.returncode}): {completed.stderr.strip()[:200]}"
            )
        try:
            data = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise MediaProbeError("ffprobe emitted invalid JSON") from exc
        if not isinstance(data, dict):
            raise MediaProbeError("ffprobe emitted an unexpected payload")
        streams = data.get("streams")
        if not isinstance(streams, list):
            raise MediaProbeError("ffprobe reported no streams")
        video = next(
            (s for s in streams if isinstance(s, dict) and s.get("codec_type") == "video"),
            None,
        )
        audio = next(
            (s for s in streams if isinstance(s, dict) and s.get("codec_type") == "audio"),
            None,
        )
        if video is None:
            raise MediaProbeError("no video stream found")
        duration_raw = (
            data.get("format", {}).get("duration") if isinstance(data.get("format"), dict) else None
        )
        try:
            duration = float(duration_raw) if duration_raw is not None else 0.0
        except (TypeError, ValueError) as exc:
            raise MediaProbeError("ffprobe returned invalid duration") from exc
        try:
            fps = _parse_fraction(video.get("avg_frame_rate"), "avg_frame_rate")
        except MediaProbeError:
            fps = _parse_fraction(video.get("r_frame_rate"), "r_frame_rate")
        width = video.get("width")
        height = video.get("height")
        if not isinstance(width, int) or not isinstance(height, int):
            raise MediaProbeError("ffprobe returned no video dimensions")
        sample_rate = 48000
        channels = 2
        if audio is not None:
            raw_rate = audio.get("sample_rate")
            raw_channels = audio.get("channels")
            if isinstance(raw_rate, str) and raw_rate.isdigit():
                sample_rate = int(raw_rate)
            elif isinstance(raw_rate, int):
                sample_rate = raw_rate
            if isinstance(raw_channels, int) and raw_channels >= 1:
                channels = raw_channels
        return MediaInfo(
            duration=duration,
            width=width,
            height=height,
            fps=fps,
            sample_rate=sample_rate,
            channels=channels,
        )
