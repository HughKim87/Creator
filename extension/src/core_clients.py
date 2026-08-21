"""Maintainer Extension이 Agent Core 공개 CLI만 호출하는 adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


DEFAULT_STORAGE_ROOT = "extension/data/shared-data"
DEFAULT_PROTECTED_PATHS = ("inputs", "outputs", "extension/inputs", "extension/outputs")


class CoreClientError(RuntimeError):
    def __init__(self, message: str, *, kind: str = "core_client_error", recoverable: bool = False) -> None:
        super().__init__(message)
        self.kind = kind
        self.recoverable = recoverable


class SharedDataLimitError(CoreClientError):
    pass


def _core_root(value: Path | str | None = None) -> Path:
    root = Path(value) if value is not None else Path(__file__).resolve().parents[2] / "core"
    resolved = root.resolve()
    if not resolved.is_dir():
        raise CoreClientError(f"Core root가 없다: {resolved}")
    return resolved


def _environment(core_root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(core_root), str(core_root / "src"), existing]
    ).rstrip(os.pathsep)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONUTF8"] = "1"
    return environment


def _run_json(
    command: list[str], *, core_root: Path, input_value: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=core_root,
        env=_environment(core_root),
        input=None if input_value is None else json.dumps(input_value, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise CoreClientError(
            completed.stderr.strip() or "Core CLI가 JSON을 반환하지 않았다",
            kind="invalid_core_response",
        ) from exc
    if not isinstance(payload, dict):
        raise CoreClientError("Core CLI 응답이 object가 아니다", kind="invalid_core_response")
    if completed.returncode != 0 or payload.get("ok") is not True:
        kind = str(payload.get("kind", "core_cli_failure"))
        error = str(payload.get("error", completed.stderr.strip() or "Core CLI 실패"))
        error_type = SharedDataLimitError if kind == "evidence_context_limit" else CoreClientError
        raise error_type(
            error,
            kind=kind,
            recoverable=bool(payload.get("recoverable", False)),
        )
    return payload


def public_core_manifest(core_root: Path | str | None = None) -> dict[str, Any]:
    """내부 Python import 없이 공개 verify와 shared_data info만 결합한다."""

    root = _core_root(core_root)
    verified = _run_json(
        [sys.executable, "-B", "-m", "core_check", "--core-root", str(root), "verify"],
        core_root=root,
    )
    info = _run_json(
        [sys.executable, "-B", "-m", "experimental.shared_data", "info"],
        core_root=root,
    )
    contract = verified.get("contract_version")
    capability_version = info.get("capability_version")
    return {
        "manifest_version": 1,
        "core_revision": f"contract-{contract}:shared_data-{capability_version}",
        "contract_version": contract,
        "capability": info.get("capability"),
        "capability_version": capability_version,
        "commands": info.get("commands"),
        "operations": info.get("operations"),
        "request_schema": info.get("request_schema"),
        "result_schema": info.get("result_schema"),
    }


class SharedDataClient:
    def __init__(
        self,
        consumer_root: Path | str,
        *,
        core_root: Path | str | None = None,
        storage_root: str = DEFAULT_STORAGE_ROOT,
        protected_paths: Sequence[str] = DEFAULT_PROTECTED_PATHS,
    ) -> None:
        self.consumer_root = Path(consumer_root).resolve()
        if not self.consumer_root.is_dir():
            raise CoreClientError(f"consumer root가 없다: {self.consumer_root}")
        self.core_root = _core_root(core_root)
        self.storage_root = storage_root
        self.protected_paths = tuple(protected_paths)

    def info(self) -> dict[str, Any]:
        return _run_json(
            [sys.executable, "-B", "-m", "experimental.shared_data", "info"],
            core_root=self.core_root,
        )

    def invoke(
        self, operation: str, arguments: Mapping[str, Any], *, write: bool = False
    ) -> Any:
        command = [
            sys.executable,
            "-B",
            "-m",
            "experimental.shared_data",
            "--consumer-root",
            str(self.consumer_root),
            "--storage-root",
            self.storage_root,
        ]
        for protected in self.protected_paths:
            command.extend(["--protected-path", protected])
        if write:
            command.append("--write")
        command.append("invoke")
        payload = _run_json(
            command,
            core_root=self.core_root,
            input_value={"operation": operation, "arguments": dict(arguments)},
        )
        return payload["result"]
