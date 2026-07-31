"""Verify ignored local runtime capabilities without making them clone requirements."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any
from urllib.parse import urlparse
import wave


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "extension" / "config" / "local-runtime-v1.json"
_ROOT_KEYS = {
    "$schema",
    "schema_version",
    "runtime_root",
    "retention",
    "tree_digest",
    "verified_on",
    "components",
}
_COMPONENT_KEYS = {
    "id",
    "status",
    "role",
    "version",
    "platform",
    "relative_root",
    "file_count",
    "bytes",
    "tree_sha256",
    "critical_files",
    "probe",
    "source",
}
_CRITICAL_KEYS = {"role", "path", "bytes", "sha256"}
_SOURCE_REQUIRED_KEYS = {
    "project_url",
    "distribution_url",
    "release_label",
    "source_commit",
    "license",
    "license_path",
    "reinstall",
}
_SOURCE_OPTIONAL_KEYS = {"model_url", "model_sha1"}
_ALLOWED_STATUSES = {"retained-shared-tool", "retained-optional-backend"}
_ALLOWED_PROBES = {"ffmpeg", "whisper_cpp", "none"}
_COMPONENT_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_HEX_COMMIT = re.compile(r"^[0-9a-f]{7,40}$")
_SHA1 = re.compile(r"^[0-9a-f]{40}$")


class RuntimeManifestError(ValueError):
    """Raised when the tracked runtime contract is malformed or unsafe."""


def _safe_relative(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RuntimeManifestError(f"{label} must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ":" in path.parts[0] or ".." in path.parts:
        raise RuntimeManifestError(f"{label} must stay inside its declared root")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise RuntimeManifestError(f"{label} must be lowercase SHA-256")
    return value


def _non_empty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RuntimeManifestError(f"{label} must be a non-empty string")
    return value


def _http_url(value: object, label: str) -> str:
    url = _non_empty_string(value, label)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeManifestError(f"{label} must be an HTTP(S) URL")
    return url


def _validate_source(value: object, label: str) -> None:
    if not isinstance(value, dict):
        raise RuntimeManifestError(f"{label} must be an object")
    keys = set(value)
    if not _SOURCE_REQUIRED_KEYS.issubset(keys) or not keys.issubset(
        _SOURCE_REQUIRED_KEYS | _SOURCE_OPTIONAL_KEYS
    ):
        raise RuntimeManifestError(
            f"{label} must contain required source metadata and only known keys"
        )
    if ("model_url" in value) != ("model_sha1" in value):
        raise RuntimeManifestError(
            f"{label}.model_url and model_sha1 must be declared together"
        )
    _http_url(value["project_url"], f"{label}.project_url")
    _http_url(value["distribution_url"], f"{label}.distribution_url")
    _non_empty_string(value["release_label"], f"{label}.release_label")
    source_commit = value["source_commit"]
    if not isinstance(source_commit, str) or not _HEX_COMMIT.fullmatch(source_commit):
        raise RuntimeManifestError(f"{label}.source_commit must be 7-40 lowercase hex")
    _non_empty_string(value["license"], f"{label}.license")
    license_path = value["license_path"]
    if license_path is not None:
        _safe_relative(license_path, f"{label}.license_path")
    _non_empty_string(value["reinstall"], f"{label}.reinstall")
    if "model_url" in value:
        _http_url(value["model_url"], f"{label}.model_url")
        model_sha1 = value["model_sha1"]
        if not isinstance(model_sha1, str) or not _SHA1.fullmatch(model_sha1):
            raise RuntimeManifestError(f"{label}.model_sha1 must be lowercase SHA-1")


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Load and validate the dependency-free subset needed by the verifier."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeManifestError(f"cannot read runtime manifest: {error}") from error
    if not isinstance(value, dict) or set(value) != _ROOT_KEYS:
        raise RuntimeManifestError(f"manifest must contain exactly: {sorted(_ROOT_KEYS)}")
    if value["$schema"] != "../schemas/local-runtime-v1.schema.json":
        raise RuntimeManifestError("runtime schema reference is not supported")
    if value["schema_version"] != "local-runtime-v1":
        raise RuntimeManifestError("unsupported runtime schema version")
    if value["runtime_root"] != "extension/.runtime":
        raise RuntimeManifestError("runtime_root must be extension/.runtime")
    if value["retention"] != "gitignored-local-capability":
        raise RuntimeManifestError("runtime retention must stay gitignored-local-capability")
    if (
        value["tree_digest"]
        != "sha256(sorted-posix-path-ordinal|bytes|sha256-with-lf)"
    ):
        raise RuntimeManifestError("runtime tree digest contract is not supported")
    verified_on = value["verified_on"]
    if not isinstance(verified_on, str):
        raise RuntimeManifestError("verified_on must be an ISO date")
    try:
        date.fromisoformat(verified_on)
    except ValueError as error:
        raise RuntimeManifestError("verified_on must be an ISO date") from error
    components = value["components"]
    if not isinstance(components, list) or not components:
        raise RuntimeManifestError("components must be a non-empty list")
    ids: set[str] = set()
    for index, component in enumerate(components):
        label = f"components[{index}]"
        if not isinstance(component, dict) or set(component) != _COMPONENT_KEYS:
            raise RuntimeManifestError(
                f"{label} must contain exactly: {sorted(_COMPONENT_KEYS)}"
            )
        component_id = component["id"]
        if (
            not isinstance(component_id, str)
            or not _COMPONENT_ID.fullmatch(component_id)
            or component_id in ids
        ):
            raise RuntimeManifestError(
                "component ids must be unique lowercase identifiers"
            )
        ids.add(component_id)
        if component["status"] not in _ALLOWED_STATUSES:
            raise RuntimeManifestError(f"{label}.status is not allowed")
        _non_empty_string(component["role"], f"{label}.role")
        _non_empty_string(component["version"], f"{label}.version")
        if component["platform"] != "windows-x86_64":
            raise RuntimeManifestError(f"{label}.platform must be windows-x86_64")
        _safe_relative(component["relative_root"], f"{label}.relative_root")
        if not isinstance(component["file_count"], int) or component["file_count"] < 1:
            raise RuntimeManifestError(f"{label}.file_count must be positive")
        if not isinstance(component["bytes"], int) or component["bytes"] < 1:
            raise RuntimeManifestError(f"{label}.bytes must be positive")
        _validate_sha256(component["tree_sha256"], f"{label}.tree_sha256")
        critical = component["critical_files"]
        if not isinstance(critical, list) or not critical:
            raise RuntimeManifestError(f"{label}.critical_files must be non-empty")
        roles: set[str] = set()
        for critical_index, item in enumerate(critical):
            item_label = f"{label}.critical_files[{critical_index}]"
            if not isinstance(item, dict) or set(item) != _CRITICAL_KEYS:
                raise RuntimeManifestError(
                    f"{item_label} must contain exactly: {sorted(_CRITICAL_KEYS)}"
                )
            if not isinstance(item["role"], str) or not item["role"] or item["role"] in roles:
                raise RuntimeManifestError("critical file roles must be unique")
            roles.add(item["role"])
            _safe_relative(item["path"], f"{item_label}.path")
            if not isinstance(item["bytes"], int) or item["bytes"] < 1:
                raise RuntimeManifestError(f"{item_label}.bytes must be positive")
            _validate_sha256(item["sha256"], f"{item_label}.sha256")
        probe = component["probe"]
        if not isinstance(probe, dict) or set(probe) != {"kind"}:
            raise RuntimeManifestError(f"{label}.probe must contain only kind")
        if probe["kind"] not in _ALLOWED_PROBES:
            raise RuntimeManifestError(f"{label}.probe kind is not allowed")
        _validate_source(component["source"], f"{label}.source")
    return value


def tree_record(root: Path) -> dict[str, Any]:
    """Return the canonical file count, byte count, and tree digest."""

    rows: list[str] = []
    total = 0
    files = [path for path in root.rglob("*") if path.is_file()]
    for path in files:
        if path.is_symlink():
            raise RuntimeManifestError(f"runtime file must not be a symlink: {path}")
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        total += size
        rows.append(f"{relative}|{size}|{_sha256(path)}")
    rows.sort()
    payload = ("\n".join(rows) + "\n").encode("utf-8")
    return {
        "file_count": len(files),
        "bytes": total,
        "tree_sha256": hashlib.sha256(payload).hexdigest(),
    }


def _critical_paths(component: dict[str, Any], component_root: Path) -> dict[str, Path]:
    return {
        item["role"]: component_root.joinpath(*PurePosixPath(item["path"]).parts)
        for item in component["critical_files"]
    }


def _run(command: list[str], *, cwd: Path, timeout: int = 120) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": f"{type(error).__name__}: {error}",
        }

    def bounded(value: str, limit: int = 2000) -> str:
        if len(value) <= limit:
            return value
        edge = limit // 2
        return value[:edge] + "\n...<truncated>...\n" + value[-edge:]

    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": bounded(completed.stdout),
        "stderr": bounded(completed.stderr),
    }


def _write_silence(path: Path) -> None:
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(16000)
        target.writeframes(b"\x00\x00" * 8000)


def _probe_ffmpeg(
    component: dict[str, Any],
    component_root: Path,
) -> dict[str, Any]:
    paths = _critical_paths(component, component_root)
    version = _run([str(paths["ffmpeg"]), "-version"], cwd=component_root)
    probe_version = _run([str(paths["ffprobe"]), "-version"], cwd=component_root)
    with tempfile.TemporaryDirectory(prefix="local-runtime-ffmpeg-") as temp:
        audio = Path(temp) / "silence.wav"
        create = _run(
            [
                str(paths["ffmpeg"]),
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=16000:cl=mono",
                "-t",
                "0.25",
                "-y",
                str(audio),
            ],
            cwd=component_root,
        )
        inspect = _run(
            [
                str(paths["ffprobe"]),
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_type,sample_rate",
                "-of",
                "json",
                str(audio),
            ],
            cwd=component_root,
        )
    expected = component["version"]
    checks = {
        "ffmpeg_version": version["ok"] and expected in version["stdout"],
        "ffprobe_version": probe_version["ok"] and expected in probe_version["stdout"],
        "synthetic_audio": create["ok"] and inspect["ok"] and '"codec_type": "audio"' in inspect["stdout"],
    }
    return {"ok": all(checks.values()), "checks": checks}


def _probe_whisper(
    component: dict[str, Any],
    component_root: Path,
) -> dict[str, Any]:
    paths = _critical_paths(component, component_root)
    cli = paths["whisper_cli"]
    help_result = _run([str(cli), "-h"], cwd=cli.parent)
    with tempfile.TemporaryDirectory(prefix="local-runtime-whisper-") as temp:
        audio = Path(temp) / "silence.wav"
        output = Path(temp) / "transcript"
        _write_silence(audio)
        relative_model = Path("..") / paths["model"].relative_to(component_root)
        model_load = _run(
            [
                str(cli),
                "-m",
                str(relative_model),
                "-f",
                str(audio),
                "-l",
                "en",
                "-ng",
                "-nt",
                "-np",
                "-otxt",
                "-of",
                str(output),
            ],
            cwd=cli.parent,
        )
        transcript_created = output.with_suffix(".txt").is_file()
    checks = {
        "cli_help": help_result["ok"] and "whisper-cli" in (
            help_result["stdout"] + help_result["stderr"]
        ),
        "model_load": model_load["ok"] and transcript_created,
    }
    return {"ok": all(checks.values()), "checks": checks}


def verify_runtime(
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    runtime_root: Path | None = None,
    require_present: bool = False,
    run_probes: bool = False,
) -> dict[str, Any]:
    """Verify manifest structure and local capability state."""

    manifest = load_manifest(manifest_path)
    if runtime_root is None:
        runtime_root = ROOT.joinpath(
            *PurePosixPath(manifest["runtime_root"]).parts
        )
    component_results: list[dict[str, Any]] = []
    for component in manifest["components"]:
        relative_root = PurePosixPath(component["relative_root"])
        component_root = runtime_root.joinpath(*relative_root.parts)
        result: dict[str, Any] = {
            "id": component["id"],
            "declared_status": component["status"],
        }
        if not component_root.exists():
            result.update({"status": "absent", "ok": not require_present})
            component_results.append(result)
            continue
        if not component_root.is_dir() or component_root.is_symlink():
            result.update({"status": "drift", "ok": False, "errors": ["unsafe root"]})
            component_results.append(result)
            continue
        actual = tree_record(component_root)
        errors = [
            field
            for field in ("file_count", "bytes", "tree_sha256")
            if actual[field] != component[field]
        ]
        for expected in component["critical_files"]:
            critical = component_root.joinpath(
                *PurePosixPath(expected["path"]).parts
            )
            if not critical.is_file():
                errors.append(f"missing:{expected['role']}")
                continue
            if critical.stat().st_size != expected["bytes"]:
                errors.append(f"bytes:{expected['role']}")
            if _sha256(critical) != expected["sha256"]:
                errors.append(f"sha256:{expected['role']}")
        result.update({"actual": actual, "errors": errors})
        if errors:
            result.update({"status": "drift", "ok": False})
        else:
            result.update({"status": "ready", "ok": True})
            if run_probes:
                kind = component["probe"]["kind"]
                if kind == "ffmpeg":
                    probe = _probe_ffmpeg(component, component_root)
                elif kind == "whisper_cpp":
                    probe = _probe_whisper(component, component_root)
                else:
                    probe = {"ok": True, "checks": {}}
                result["probe"] = probe
                result["ok"] = probe["ok"]
                if not probe["ok"]:
                    result["status"] = "probe-failed"
        component_results.append(result)
    statuses = {component["status"] for component in component_results}
    if statuses == {"absent"}:
        status = "absent"
    elif "absent" in statuses:
        status = "incomplete"
    elif "probe-failed" in statuses:
        status = "probe-failed"
    elif all(component["ok"] for component in component_results):
        status = "ready"
    else:
        status = "drift"
    ok = all(component["ok"] for component in component_results)
    return {
        "ok": ok,
        "status": status,
        "runtime_root": str(runtime_root),
        "components": component_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--require-present", action="store_true")
    parser.add_argument("--probe", action="store_true")
    arguments = parser.parse_args()
    try:
        result = verify_runtime(
            arguments.manifest,
            runtime_root=arguments.runtime_root,
            require_present=arguments.require_present,
            run_probes=arguments.probe,
        )
    except RuntimeManifestError as error:
        result = {"ok": False, "status": "invalid-manifest", "error": str(error)}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
