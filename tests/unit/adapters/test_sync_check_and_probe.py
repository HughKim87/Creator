"""Pure sync-check calculations and MediaProbe port behavior."""

from __future__ import annotations

import math
import struct
from fractions import Fraction
from pathlib import Path

import pytest

from video_workflow.adapters.media_probe import (
    FfprobeMediaProbe,
    MediaInfo,
    MediaProbeError,
    StaticMediaProbe,
)
from video_workflow.adapters.sync_check import (
    HOP_SECONDS,
    SAMPLE_RATE,
    analyze_clip,
    parse_clip,
    parse_srt,
    parse_time,
    rms_windows,
    score_lags,
)


def test_time_and_clip_parsing_matches_legacy_grammar() -> None:
    assert parse_time("90") == 90.0
    assert parse_time("1:30") == 90.0
    assert parse_time("01:02:03.5") == 3723.5
    assert parse_clip("intro:10-1:00") == ("intro", 10.0, 60.0)
    with pytest.raises(ValueError):
        parse_time("1:2:3:4")


def test_srt_parsing_matches_legacy() -> None:
    text = (
        "1\n00:00:01,000 --> 00:00:02,500\n안녕하세요\n\n"
        "2\n00:01:00,250 --> 00:01:02,000\n다음 줄\n둘째 줄\n"
    )
    blocks = parse_srt(text)
    assert blocks == [
        (1.0, 2.5, "안녕하세요"),
        (60.25, 62.0, "다음 줄 둘째 줄"),
    ]
    with pytest.raises(ValueError):
        parse_srt("1\n00:00:01.000 --> 00:00:02,000\nbad\n")


def test_rms_windows_computes_windowed_rms() -> None:
    window = int(SAMPLE_RATE * HOP_SECONDS)
    loud = struct.pack(f"<{window}h", *([16384] * window))
    silent = struct.pack(f"<{window}h", *([0] * window))
    values = rms_windows(loud + silent)
    assert len(values) == 2
    assert math.isclose(values[0], 0.5, rel_tol=1e-6)
    assert values[1] == 0.0
    assert rms_windows(b"") == []


def test_analyze_clip_detects_injected_lag() -> None:
    """Loud windows shifted by +1s from subtitles -> best lag ≈ +1s."""
    lag_true = 1.0
    blocks = [(10.0, 15.0, "말"), (30.0, 34.0, "말")]
    window_start = 0.0
    count = int(60 / HOP_SECONDS)
    energy = []
    for index in range(count):
        t = window_start + index * HOP_SECONDS
        inside = any(start <= t - lag_true <= end for start, end, _ in blocks)
        energy.append(0.4 if inside else 0.001)
    result = analyze_clip(energy, blocks, "clip", window_start, "evidence/clip.json")
    assert result.status == "ok"
    assert result.best_lag_seconds is not None
    assert abs(result.best_lag_seconds - lag_true) <= 0.1
    assert result.scope == "subtitle_audio_alignment"
    assert result.failure_code is None


def test_analyze_clip_insufficient_data_is_not_success() -> None:
    empty = analyze_clip([], [], "clip", 0.0, "evidence")
    assert empty.status == "insufficient_data"
    assert empty.failure_code == "no_audio_samples"
    few = analyze_clip([0.1] * 5, [(0.0, 0.1, "x")], "clip", 0.0, "evidence")
    assert few.status == "insufficient_data"
    assert few.failure_code == "insufficient_overlap"


def test_score_lags_is_deterministic() -> None:
    blocks = [(1.0, 3.0, "a")]
    energy = [0.3 if 20 <= i <= 60 else 0.01 for i in range(200)]
    assert score_lags(energy, blocks, 0.0) == score_lags(energy, blocks, 0.0)


def test_static_probe_requires_existing_file(tmp_path: Path) -> None:
    info = MediaInfo(10.0, 1920, 1080, Fraction(30, 1), 48000, 2)
    probe = StaticMediaProbe(info)
    with pytest.raises(MediaProbeError):
        probe.probe(tmp_path / "missing.mp4")
    target = tmp_path / "media.mp4"
    target.write_bytes(b"data")
    assert probe.probe(target) == info


def test_ffprobe_probe_fails_closed_without_executable(tmp_path: Path) -> None:
    """No ffprobe -> structured failure, never legacy silent defaults."""
    target = tmp_path / "media.mp4"
    target.write_bytes(b"data")
    probe = FfprobeMediaProbe(executable=str(tmp_path / "no-such-ffprobe"))
    with pytest.raises((MediaProbeError, OSError)):
        probe.probe(target)


def test_media_info_rejects_invalid_values() -> None:
    with pytest.raises(MediaProbeError):
        MediaInfo(0.0, 1920, 1080, Fraction(30, 1), 48000, 2)
    with pytest.raises(MediaProbeError):
        MediaInfo(10.0, 1920, 1080, Fraction(0, 1), 48000, 2)
    with pytest.raises(MediaProbeError):
        MediaInfo(10.0, 1920, 1080, Fraction(30, 1), 48000, 0)
