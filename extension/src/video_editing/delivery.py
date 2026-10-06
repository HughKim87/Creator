from __future__ import annotations

from collections.abc import Iterable, Mapping
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any, BinaryIO, Callable, Iterator

from .premiere_xml import PREMIERE_CS6_V4_PROFILE, PremiereXmlError, _build_premiere_xml, _build_premiere_cs6_v4
from .preflight import validate_preflight
from .editorial_state import validate_editorial_state
from .timeline_v2 import (
    TimelineV2Error,
    as_legacy_timeline,
    delivery_fingerprint,
    editorial_fingerprint,
    payload_fingerprint,
    task_payload_fingerprint,
    validate_timeline_v2,
)


def _resolved(path: Path | str) -> Path:
    return Path(path).resolve(strict=False)


def _same_path(left: Path | str, right: Path | str) -> bool:
    return os.path.normcase(str(_resolved(left))) == os.path.normcase(
        str(_resolved(right))
    )


def _sha256_handle(handle: BinaryIO) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    handle.seek(0)
    while chunk := handle.read(1024 * 1024):
        digest.update(chunk)
        size += len(chunk)
    handle.seek(0)
    return "sha256:" + digest.hexdigest(), size


@contextmanager
def _locked_source(path: Path) -> Iterator[BinaryIO]:
    if os.name != "nt":
        raise PremiereXmlError(
            "this platform cannot guarantee a mandatory immutable source snapshot"
        )
    import ctypes
    import msvcrt

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    )
    create_file.restype = ctypes.c_void_p
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (ctypes.c_void_p,)
    close_handle.restype = ctypes.c_int
    os_handle = create_file(
        str(path),
        0x80000000,
        0x00000001,
        None,
        3,
        0x00000080 | 0x08000000,
        None,
    )
    if os_handle == ctypes.c_void_p(-1).value:
        error = ctypes.get_last_error()
        raise PremiereXmlError(
            f"cannot acquire a mandatory source snapshot handle (winerror={error})"
        )
    try:
        descriptor = msvcrt.open_osfhandle(
            int(os_handle), os.O_RDONLY | getattr(os, "O_BINARY", 0)
        )
    except OSError as exc:
        close_handle(os_handle)
        raise PremiereXmlError(
            "cannot convert the source snapshot handle"
        ) from exc
    with os.fdopen(descriptor, "rb") as handle:
        yield handle


def _write_no_clobber(
    target: Path,
    rendered: bytes,
    *,
    pre_publish: Callable[[], None] | None = None,
) -> None:
    if not target.parent.is_dir():
        raise PremiereXmlError(f"output directory does not exist: {target.parent}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        if pre_publish is not None:
            pre_publish()
        try:
            os.link(temporary, target)
        except FileExistsError as exc:
            raise PremiereXmlError(f"output already exists: {target}") from exc
        except OSError as exc:
            raise PremiereXmlError(
                "filesystem cannot provide atomic no-clobber delivery"
            ) from exc
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _write_guarded_premiere_xml(
    value: Mapping[str, Any],
    output_path: Path | str,
    *,
    profile: str,
    review_preflight: Mapping[str, Any] | None = None,
    editorial_state: Mapping[str, Any] | None = None,
    input_paths: Iterable[Path | str] = (),
    calibration_reference: Mapping[str, Any] | None = None,
    baseline_reference: Mapping[str, Any] | None = None,
    reference_payloads: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    reference_payloads = tuple(reference_payloads)
    purpose = "premiere_review_xml" if review_preflight is not None else "premiere_xml"
    try:
        timeline = validate_timeline_v2(
            value,
            purpose=purpose,
            calibration_reference=calibration_reference,
            baseline_reference=baseline_reference,
            reference_payloads=reference_payloads,
        )
    except TimelineV2Error:
        raise

    editorial_check = validate_editorial_state(timeline, editorial_state)
    if review_preflight is not None:
        validate_preflight(timeline, review_preflight, editorial_state)
    requested_target = Path(output_path)
    if not requested_target.is_absolute():
        raise PremiereXmlError(
            "requested output path must be an absolute canonical path"
        )
    target = _resolved(requested_target)
    if os.path.normcase(str(requested_target)) != os.path.normcase(str(target)):
        raise PremiereXmlError(
            "requested output path must identify its canonical destination"
        )
    delivery = timeline["delivery"]
    declared_output = Path(delivery["output_path"])
    if not declared_output.is_absolute():
        raise PremiereXmlError(
            "timeline.delivery.output_path must be an absolute canonical path"
        )
    declared_target = _resolved(declared_output)
    if os.path.normcase(str(declared_output)) != os.path.normcase(
        str(declared_target)
    ):
        raise PremiereXmlError(
            "timeline.delivery.output_path must identify its canonical destination"
        )
    if not _same_path(target, declared_target):
        raise PremiereXmlError(
            "output path must exactly match timeline.delivery.output_path"
        )
    if target.suffix.lower() != ".xml":
        raise PremiereXmlError("validated delivery output must end in .xml")
    if profile != delivery["profile"] or profile != PREMIERE_CS6_V4_PROFILE:
        raise PremiereXmlError(
            "profile must exactly match timeline.delivery.profile"
        )
    if delivery["overwrite"] is not False:
        raise PremiereXmlError("validated delivery never permits overwrite")
    for input_path in input_paths:
        if _same_path(target, input_path):
            raise PremiereXmlError("output path collides with an input file")

    declared_source_path = Path(timeline["source_manifest"]["path"])
    if not declared_source_path.is_absolute():
        raise PremiereXmlError(
            "source_manifest.path must be an absolute canonical path for delivery"
        )
    source_path = _resolved(declared_source_path)
    if os.path.normcase(str(declared_source_path)) != os.path.normcase(
        str(source_path)
    ):
        raise PremiereXmlError(
            "source_manifest.path must identify the canonical path that XML will reference"
        )
    if _same_path(target, source_path):
        raise PremiereXmlError("output path collides with source media")
    with _locked_source(source_path) as source_handle:
        actual_hash, actual_size = _sha256_handle(source_handle)
        if actual_hash != timeline["source_manifest"]["content_sha256"]:
            raise PremiereXmlError("source media SHA-256 does not match source_manifest")
        if actual_size != timeline["source_manifest"]["byte_size"]:
            raise PremiereXmlError("source media byte size does not match source_manifest")

        legacy_timeline = as_legacy_timeline(
            timeline,
            purpose=purpose,
            calibration_reference=calibration_reference,
            baseline_reference=baseline_reference,
            reference_payloads=reference_payloads,
        )
        legacy_timeline["source"]["path"] = str(source_path)
        rendered = (_build_premiere_cs6_v4(legacy_timeline, review_candidate=True)
                    if review_preflight is not None else _build_premiere_xml(legacy_timeline, profile=profile))

        def verify_source_snapshot() -> None:
            final_hash, final_size = _sha256_handle(source_handle)
            if final_hash != actual_hash or final_size != actual_size:
                raise PremiereXmlError("source media changed during XML generation")

        verify_source_snapshot()
        _write_no_clobber(
            target,
            rendered,
            pre_publish=verify_source_snapshot,
        )
    return {
        "output": str(target),
        "delivery_kind": "review_candidate" if review_preflight is not None else "semantically_reviewed",
        "agent_preflight_status": "recorded" if review_preflight is not None else "not_applicable",
        "editorial_structure": editorial_check,
        "bytes": len(rendered),
        "sha256": hashlib.sha256(rendered).hexdigest(),
        "payload_fingerprint": payload_fingerprint(timeline),
        "task_payload_fingerprint": task_payload_fingerprint(timeline),
        "editorial_fingerprint": editorial_fingerprint(timeline),
        "delivery_fingerprint": delivery_fingerprint(timeline),
        "source_content_sha256": actual_hash,
        "source_references": 1,
        "profile": profile,
        "validation_status": timeline["validation"]["semantic_status"],
        "revision_status": timeline["revision"]["status"],
        "user_approval_status": (
            "approved"
            if any(
                decision["decision"] == "approved"
                and decision["artifact_id"] == timeline["timeline_id"]
                and not decision["invalidated_by"]
                for decision in timeline["approval"]["decisions"]
            )
            else "not_approved"
        ),
    }


def write_validated_premiere_xml(value, output_path, *, profile, editorial_state=None, input_paths=(), calibration_reference=None, baseline_reference=None, reference_payloads=()):
    """Export after existing semantic gates and the source-scene/feedback guard."""
    return _write_guarded_premiere_xml(value, output_path, profile=profile, editorial_state=editorial_state, input_paths=input_paths,
        calibration_reference=calibration_reference, baseline_reference=baseline_reference, reference_payloads=reference_payloads)


def write_review_premiere_xml(value, output_path, *, preflight, profile, editorial_state=None, input_paths=(), calibration_reference=None, baseline_reference=None, reference_payloads=()):
    """Export an inspected, explicitly unapproved candidate for user playback."""
    if not isinstance(preflight, Mapping):
        raise PremiereXmlError("review preflight record is required")
    return _write_guarded_premiere_xml(value, output_path, profile=profile, editorial_state=editorial_state, review_preflight=preflight,
        input_paths=input_paths, calibration_reference=calibration_reference, baseline_reference=baseline_reference,
        reference_payloads=reference_payloads)
