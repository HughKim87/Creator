"""Internal Stage-0 fixture renderer; never grants semantic or application approval.

Supported: one CFR source, sample-aligned cuts, contiguous independent A/V
tracks, normal speed, no effects. Protected production media is intentionally
out of scope until the perceptual reviewer and application route are proven.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from .delivery import _locked_source, _sha256_handle
from .timeline_v2 import editorial_fingerprint, validate_timeline_v2


class ReviewProxyError(ValueError):
    """The declared render cannot be reproduced within this implementation."""


def _digest(path: Path) -> tuple[str, int]:
    with path.open("rb") as handle:
        return _sha256_handle(handle)


def _canonical_path(path: Path | str) -> Path:
    raw = Path(path)
    if not raw.is_absolute():
        raise ReviewProxyError("an absolute canonical path is required")
    # Reject protected lexical paths before resolving or touching their targets.
    if any(part.casefold() in {"inputs", "outputs"} for part in raw.parts):
        raise ReviewProxyError("Stage-0 renderer cannot access protected media")
    resolved = raw.resolve()
    if os.path.normcase(str(raw)) != os.path.normcase(str(resolved)):
        raise ReviewProxyError("symlink, junction or non-canonical path is unsupported")
    if any(part.casefold() in {"inputs", "outputs"} for part in resolved.parts):
        raise ReviewProxyError("resolved protected media is out of scope")
    return resolved


def _inside(path: Path, root: Path) -> None:
    if path == root or root not in path.parents:
        raise ReviewProxyError("fixture files must be inside the exact scratch root")


def _run(arguments: list[str], *, cwd: Path, timeout: float = 120) -> bytes:
    completed = subprocess.run(
        arguments, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True,
        timeout=timeout, check=False,
    )
    if completed.returncode:
        detail = completed.stderr.decode("utf-8", errors="replace")[-2000:]
        raise ReviewProxyError(f"tool failed ({completed.returncode}): {detail}")
    return completed.stdout


def _probe(binary: Path, media: Path, scratch: Path) -> dict[str, Any]:
    value = json.loads(_run([
        str(binary), "-v", "error", "-count_frames", "-show_streams",
        "-of", "json", str(media),
    ], cwd=scratch))
    streams = value.get("streams", [])
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    if len(videos) != 1 or len(audios) != 1 or len(streams) != 2:
        raise ReviewProxyError("exactly one video and one audio stream are supported")
    return {"video": videos[0], "audio": audios[0]}


def toolchain(consumer_root: Path) -> dict[str, Any]:
    """Resolve only the managed FFmpeg component, not optional transcription."""
    root = _canonical_path(consumer_root)
    manifest = json.loads((root / "extension/config/local-runtime-v1.json").read_text("utf-8"))
    candidates = [c for c in manifest["components"] if c["probe"]["kind"] == "ffmpeg"]
    if len(candidates) != 1:
        raise ReviewProxyError("one managed FFmpeg component is required")
    component = candidates[0]
    component_root = _canonical_path(root / manifest["runtime_root"] / component["relative_root"])
    _inside(component_root, root / "extension")
    result: dict[str, Any] = {"version": component["version"]}
    for role in ("ffmpeg", "ffprobe"):
        entries = [e for e in component["critical_files"] if e["role"] == role]
        if len(entries) != 1:
            raise ReviewProxyError(f"missing managed role: {role}")
        entry = entries[0]
        path = _canonical_path(component_root / entry["path"])
        _inside(path, component_root)
        measured = _digest(path)
        if measured != ("sha256:" + entry["sha256"], entry["bytes"]):
            raise ReviewProxyError(f"managed binary drift: {role}")
        version = _run([str(path), "-version"], cwd=root).decode("utf-8")
        if component["version"] not in version.splitlines()[0]:
            raise ReviewProxyError(f"unexpected binary version: {role}")
        result[role] = path
        result[role + "_sha256"] = measured[0]
    return result


def render_spec(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate metadata without requiring or manufacturing semantic approval."""
    timeline = validate_timeline_v2(value)
    if timeline["revision"]["status"] != "working_candidate":
        raise ReviewProxyError("Stage-0 requires a working candidate, not a baseline")
    source = timeline["source_manifest"]
    rate = Fraction(source["frame_rate"]["numerator"], source["frame_rate"]["denominator"])
    samples_per_frame = Fraction(source["audio"]["sample_rate"], 1) / rate
    if samples_per_frame.denominator != 1:
        raise ReviewProxyError("fractional sample boundaries are not yet supported")
    if source["audio"]["channels"] not in {1, 2}:
        raise ReviewProxyError("only mono/stereo sources are supported")
    graph: list[str] = []
    for kind, selector, clips in (
        ("v", "v:0", timeline["sequence"]["video_clips"]),
        ("a", "a:0", timeline["sequence"]["audio_clips"]),
    ):
        labels = []
        for index, clip in enumerate(clips):
            if clip["gap_before"]:
                raise ReviewProxyError("audio holes cannot be replaced with synthetic silence")
            start, end = clip["source_in"], clip["source_out"]
            if kind == "v":
                operation = f"trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS"
            else:
                operation = (
                    f"atrim=start_sample={start * int(samples_per_frame)}:"
                    f"end_sample={end * int(samples_per_frame)},asetpts=PTS-STARTPTS"
                )
            label = f"{kind}{index}"
            graph.append(f"[0:{selector}]{operation}[{label}]")
            labels.append(f"[{label}]")
        graph.append("".join(labels) + f"concat=n={len(clips)}:v={int(kind == 'v')}:a={int(kind == 'a')}[{kind}out]")
    total = timeline["sequence"]["video_clips"][-1]["timeline_end"]
    return {
        "timeline": timeline, "graph": ";".join(graph), "frames": total,
        "samples": total * int(samples_per_frame), "rate": rate,
        "editorial_fingerprint": editorial_fingerprint(timeline),
    }


def _check_streams(observed: dict[str, Any], source: dict[str, Any], frames: int) -> None:
    video, audio = observed["video"], observed["audio"]
    expected_rate = Fraction(source["frame_rate"]["numerator"], source["frame_rate"]["denominator"])
    try:
        valid = (
            int(video["nb_read_frames"]) == frames
            and Fraction(video["avg_frame_rate"]) == expected_rate
            and Fraction(video["r_frame_rate"]) == expected_rate
            and video["width"] == source["video"]["width"]
            and video["height"] == source["video"]["height"]
            and int(audio["sample_rate"]) == source["audio"]["sample_rate"]
            and audio["channels"] == source["audio"]["channels"]
            and Fraction(video.get("start_time", "0")) == 0
            and Fraction(audio.get("start_time", "0")) == 0
        )
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        raise ReviewProxyError("unmeasurable media metadata") from exc
    if not valid:
        raise ReviewProxyError("measured frames/rate/geometry/audio do not match the render contract")


def _check_timestamps(binary: Path, media: Path, scratch: Path, observed: dict[str, Any], rate: Fraction) -> None:
    # avg_frame_rate == r_frame_rate alone does not establish CFR or continuous audio.
    for kind in ("video", "audio"):
        selector = "v:0" if kind == "video" else "a:0"
        data = json.loads(_run([
            str(binary), "-v", "error", "-select_streams", selector,
            "-show_frames", "-show_entries", "frame=best_effort_timestamp_time,nb_samples",
            "-of", "json", str(media),
        ], cwd=scratch))
        frames = data.get("frames", [])
        if not frames:
            raise ReviewProxyError("missing decoded timestamp evidence")
        units = 0
        clock = rate if kind == "video" else Fraction(int(observed["audio"]["sample_rate"]))
        tick = Fraction(observed[kind]["time_base"])
        for frame in frames:
            try:
                timestamp = Fraction(frame["best_effort_timestamp_time"])
                count = 1 if kind == "video" else int(frame["nb_samples"])
            except (KeyError, ValueError) as exc:
                raise ReviewProxyError("unmeasurable decoded timestamp") from exc
            # Container timestamp quantization is not an editorial tolerance.
            if count < 1 or abs(timestamp - units / clock) > tick:
                raise ReviewProxyError("variable frame cadence or discontinuous audio is unsupported")
            units += count


def render_fixture_proxy(
    value: Mapping[str, Any], *, consumer_root: Path, scratch_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Render a non-deliverable lossless MKV; return technical evidence only."""
    root = _canonical_path(consumer_root)
    scratch = _canonical_path(scratch_root)
    _inside(scratch, root / "extension/data")
    if not scratch.is_dir():
        raise ReviewProxyError("the exact existing scratch directory is required")
    spec = render_spec(value)
    source = spec["timeline"]["source_manifest"]
    source_path = _canonical_path(source["path"])
    target = _canonical_path(output_path)
    _inside(source_path, scratch)
    _inside(target, scratch)
    if target == source_path or target.suffix.lower() != ".mkv" or target.exists():
        raise ReviewProxyError("a new non-colliding .mkv target is required")
    if not target.parent.is_dir():
        raise ReviewProxyError("target parent must exist")
    binaries = toolchain(root)
    expected_source = (source["content_sha256"], source["byte_size"])
    # The existing Windows mandatory lock permits readers but forbids writers.
    with _locked_source(source_path) as handle:
        if _sha256_handle(handle) != expected_source:
            raise ReviewProxyError("source bytes differ from manifest")
        observed_source = _probe(binaries["ffprobe"], source_path, scratch)
        _check_streams(observed_source, source, source["total_frames"])
        _check_timestamps(binaries["ffprobe"], source_path, scratch, observed_source, spec["rate"])
        with tempfile.TemporaryDirectory(prefix="proxy-render-", dir=scratch) as temporary:
            temporary_root = Path(temporary)
            rendered = temporary_root / "proxy.mkv"
            pcm = temporary_root / "measured.pcm"
            _run([
                str(binaries["ffmpeg"]), "-nostdin", "-v", "error", "-xerror",
                "-i", str(source_path), "-filter_complex", spec["graph"],
                "-map", "[vout]", "-map", "[aout]", "-c:v", "ffv1",
                "-c:a", "pcm_s16le", "-fps_mode", "passthrough", "-n", str(rendered),
            ], cwd=temporary_root)
            observed = _probe(binaries["ffprobe"], rendered, temporary_root)
            _check_streams(observed, source, spec["frames"])
            _check_timestamps(binaries["ffprobe"], rendered, temporary_root, observed, spec["rate"])
            _run([
                str(binaries["ffmpeg"]), "-nostdin", "-v", "error", "-xerror",
                "-i", str(rendered), "-map", "0:a:0", "-c:a", "pcm_s16le",
                "-f", "s16le", "-n", str(pcm),
            ], cwd=temporary_root)
            measured_samples, remainder = divmod(pcm.stat().st_size, 2 * source["audio"]["channels"])
            if remainder or measured_samples != spec["samples"]:
                raise ReviewProxyError("decoded audio sample count differs from sequence")
            if _sha256_handle(handle) != expected_source:
                raise ReviewProxyError("source drift before publication")
            proxy_hash, proxy_size = _digest(rendered)
            evidence = {
                "evidence_version": "fixture-proxy-technical-v1",
                "editorial_fingerprint": spec["editorial_fingerprint"],
                "source_sha256": expected_source[0], "source_bytes": expected_source[1],
                "proxy_path": str(target), "proxy_sha256": proxy_hash, "proxy_bytes": proxy_size,
                "frames": spec["frames"], "audio_samples": measured_samples,
                "render_graph_sha256": "sha256:" + hashlib.sha256(spec["graph"].encode()).hexdigest(),
                "tool_version": binaries["version"],
                "ffmpeg_sha256": binaries["ffmpeg_sha256"],
                "ffprobe_sha256": binaries["ffprobe_sha256"],
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "technical_status": "passed", "semantic_status": "not_run",
                "app_status": "not_run", "user_status": "not_run",
            }
            # Same-filesystem hard link is atomic and cannot replace an existing file.
            os.link(rendered, target)
    return evidence


def verify_fixture_binding(value: Mapping[str, Any], evidence: Mapping[str, Any], *, scratch_root: Path) -> dict[str, str]:
    """Check identity, not the truth of a reviewer claim or authenticity of a log."""
    spec = render_spec(value)
    scratch = _canonical_path(scratch_root)
    proxy = _canonical_path(evidence["proxy_path"])
    _inside(proxy, scratch)
    source = spec["timeline"]["source_manifest"]
    expected = {
        "evidence_version": "fixture-proxy-technical-v1",
        "editorial_fingerprint": spec["editorial_fingerprint"],
        "source_sha256": source["content_sha256"], "source_bytes": source["byte_size"],
        "frames": spec["frames"], "audio_samples": spec["samples"],
        "render_graph_sha256": "sha256:" + hashlib.sha256(spec["graph"].encode()).hexdigest(),
        "technical_status": "passed", "semantic_status": "not_run",
        "app_status": "not_run", "user_status": "not_run",
    }
    if any(evidence.get(key) != item for key, item in expected.items()):
        raise ReviewProxyError("stale or overstated technical evidence")
    if _digest(proxy) != (evidence.get("proxy_sha256"), evidence.get("proxy_bytes")):
        raise ReviewProxyError("proxy bytes changed after rendering")
    source_path = _canonical_path(source["path"])
    _inside(source_path, scratch)
    with _locked_source(source_path) as handle:
        if _sha256_handle(handle) != (source["content_sha256"], source["byte_size"]):
            raise ReviewProxyError("source bytes changed after rendering")
    return {"binding_status": "passed", "semantic_status": "not_run", "app_status": "not_run", "user_status": "not_run"}
