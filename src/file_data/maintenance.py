from __future__ import annotations

import ast
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Mapping, Sequence

from .context import ContextService
from .knowledge import KnowledgeService, SourceIntegrityError
from .lifecycle import TERMINAL_STATES, LifecycleService
from .store import InputContractError


GENERATED_INVENTORY_REF = "docs/obsidian/GENERATED_DOCUMENT_INVENTORY.md"
RUNTIME_WARNING_MS = 5_000
PROTECTED_SEGMENTS = frozenset({"backup", "inputs", "outputs", ".git", ".obsidian"})
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


class MaintenanceError(InputContractError):
    pass


class MaintenanceService:
    def __init__(self, project_root: Path | str) -> None:
        self.root = Path(project_root).resolve()
        self.safe_directory = self.root.as_posix()
        self.lifecycle = LifecycleService(self.root)
        self.knowledge = KnowledgeService(self.root)
        self.context = ContextService(self.root)

    def _git(self, *arguments: str) -> list[str]:
        result = subprocess.run(
            [
                "git", "-c", "core.quotepath=false", "-c",
                f"safe.directory={self.safe_directory}", *arguments,
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode != 0:
            raise MaintenanceError(result.stderr.strip() or "git inventory command failed")
        return result.stdout.splitlines()

    def git_status_paths(self) -> list[str]:
        paths: list[str] = []
        for line in self._git("status", "--short"):
            if len(line) < 4:
                continue
            path = line[3:].split(" -> ")[-1].replace("\\", "/")
            paths.append(path)
        return paths

    def document_refs(self, *, include_generated: bool = True) -> list[str]:
        tracked = self._git(
            "ls-files", "--", "*.md", ":(exclude)backup/**", ":(exclude)inputs/**",
            ":(exclude)outputs/**", ":(exclude).git/**", ":(exclude).obsidian/**",
        )
        changed = [path for path in self.git_status_paths() if path.endswith(".md")]
        refs: list[str] = []
        for ref in sorted(set(tracked + changed)):
            parts = set(Path(ref).parts)
            if parts & PROTECTED_SEGMENTS:
                continue
            if not include_generated and ref == GENERATED_INVENTORY_REF:
                continue
            if (self.root / ref).is_file():
                refs.append(ref)
        return refs

    def _title(self, ref: str) -> str:
        raw = (self.root / ref).read_bytes()
        try:
            content = raw.decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raise MaintenanceError(f"document is not strict UTF-8: {ref}") from exc
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return Path(ref).stem

    def render_inventory(self) -> str:
        refs = self.document_refs(include_generated=False)
        groups: dict[str, list[str]] = defaultdict(list)
        for ref in refs:
            group = Path(ref).parts[0] if len(Path(ref).parts) > 1 else "root"
            groups[group].append(ref)
        lines = [
            "# 자동 생성 활성 문서 inventory",
            "",
            "- 목적: 보호·역사 경계를 제외한 활성 Markdown 경로를 정본에서 결정론적으로 재생성한다.",
            "- 상태: 파생물. 이 파일은 규칙·상태·결정을 소유하지 않는다.",
            "- 생성 명령: `python -m file_data maintenance-inventory --write`",
            f"- 원본 문서 수: {len(refs)}",
            "- 자기 재귀 방지: 이 생성 파일 자체는 원본 목록에서 제외한다.",
            "",
        ]
        inventory_path = self.root / GENERATED_INVENTORY_REF
        for group in sorted(groups):
            lines.extend([f"## {group}", ""])
            for ref in sorted(groups[group]):
                relative = Path(os.path.relpath(self.root / ref, inventory_path.parent)).as_posix()
                lines.append(f"- [{self._title(ref)}]({relative}) — `{ref}`")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def inventory_status(self) -> dict[str, Any]:
        expected = self.render_inventory().encode("utf-8")
        target = self.root / GENERATED_INVENTORY_REF
        current = target.read_bytes() if target.is_file() else None
        return {
            "ref": GENERATED_INVENTORY_REF,
            "exists": current is not None,
            "matches": current == expected,
            "expected_bytes": len(expected),
            "current_bytes": None if current is None else len(current),
        }

    def write_inventory(self) -> dict[str, Any]:
        target = self.root / GENERATED_INVENTORY_REF
        target.parent.mkdir(parents=True, exist_ok=True)
        rendered = self.render_inventory().encode("utf-8")
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_bytes(rendered)
        temporary.replace(target)
        status = self.inventory_status()
        if not status["matches"]:
            raise MaintenanceError("generated inventory post-write verification failed")
        return status

    def detect_drift(self) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        drifted_sources: set[str] = set()
        states = self.lifecycle.list_states()
        for state in states:
            if state["payload"]["state"] in TERMINAL_STATES:
                continue
            record = self.lifecycle.store.get_record(state["payload"]["target_id"])
            try:
                if record["record_type"] == "source":
                    self.knowledge.get_source(record["id"], verify_local=True)
                elif record["record_type"] == "failure_knowledge":
                    self.knowledge.get_failure_knowledge(record["id"])
            except SourceIntegrityError as exc:
                findings.append({"target_id": record["id"], "kind": "integrity", "reason": str(exc)})
                if record["record_type"] == "source":
                    drifted_sources.add(record["id"])
        for state in states:
            if state["payload"]["state"] in TERMINAL_STATES:
                continue
            record = self.lifecycle.store.get_record(state["payload"]["target_id"])
            payload = record["payload"]
            if record["record_type"] in {"knowledge", "decision"}:
                source_ids = set(payload["source_ids"])
            elif record["record_type"] == "failure_knowledge":
                source_ids = {payload["source_id"]}
            else:
                source_ids = set()
            affected = sorted(source_ids & drifted_sources)
            if affected and not any(item["target_id"] == record["id"] for item in findings):
                findings.append(
                    {
                        "target_id": record["id"],
                        "kind": "dependency",
                        "reason": "referenced source drift: " + ", ".join(affected),
                    }
                )
        return sorted(findings, key=lambda item: (item["kind"], item["target_id"]))

    def detect_duplicates(self) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        claims: dict[str, list[str]] = defaultdict(list)
        for record in self.lifecycle.current_records(target_type="knowledge"):
            claims[record["payload"]["statement"].strip().casefold()].append(record["id"])
        for value, ids in claims.items():
            if len(ids) > 1:
                findings.append({"kind": "knowledge_statement", "value": value, "record_ids": sorted(ids)})
        failure_docs: dict[str, list[str]] = defaultdict(list)
        for record in self.lifecycle.current_records(target_type="failure_knowledge"):
            failure_docs[record["payload"]["canonical_doc_ref"]].append(record["id"])
        for value, ids in failure_docs.items():
            if len(ids) > 1:
                findings.append({"kind": "failure_document", "value": value, "record_ids": sorted(ids)})
        return sorted(findings, key=lambda item: (item["kind"], item["value"]))

    def cost_report(self, started: float | None = None) -> dict[str, Any]:
        refs = self.document_refs(include_generated=True)
        documents = self.context.measure_documents(refs)
        record_types = (
            "source", "knowledge", "decision", "failure_knowledge", "lifecycle_state", "work_state"
        )
        records = {record_type: len(self.lifecycle.store.list_records(record_type)) for record_type in record_types}
        lifecycle_events = len(self.lifecycle._events()[0])
        work_events = len(self.lifecycle.store.list_events("work_events")[0])
        elapsed = None if started is None else round((time.perf_counter() - started) * 1000, 2)
        return {
            "documents": documents,
            "records_by_type": records,
            "events": {"lifecycle": lifecycle_events, "work": work_events},
            "generated_files": 1 if (self.root / GENERATED_INVENTORY_REF).is_file() else 0,
            "elapsed_ms": elapsed,
            "runtime_warning": elapsed is not None and elapsed > RUNTIME_WARNING_MS,
        }

    def scan(self) -> dict[str, Any]:
        started = time.perf_counter()
        drift = self.detect_drift()
        duplicates = self.detect_duplicates()
        inventory = self.inventory_status()
        costs = self.cost_report(started)
        ok = not drift and not duplicates and inventory["matches"]
        return {
            "ok": ok,
            "status": "pass" if ok else "attention_required",
            "drift": drift,
            "duplicates": duplicates,
            "inventory": inventory,
            "costs": costs,
        }

    def _document_errors(self) -> tuple[list[str], int]:
        errors: list[str] = []
        links = 0
        for ref in self.document_refs(include_generated=True):
            path = self.root / ref
            raw = path.read_bytes()
            try:
                content = raw.decode("utf-8", "strict")
            except UnicodeDecodeError as exc:
                errors.append(f"utf8:{ref}:{exc}")
                continue
            if b"\x00" in raw:
                errors.append(f"nul:{ref}")
            for number, line in enumerate(content.splitlines(), 1):
                if line.rstrip(" \t") != line:
                    errors.append(f"trailing:{ref}:{number}")
            for match in LINK_PATTERN.finditer(content):
                target = match.group(1).strip().strip("<>")
                if not target or target.startswith("#") or SCHEME_PATTERN.match(target):
                    continue
                target = target.split("#", 1)[0]
                if not target:
                    continue
                links += 1
                resolved = (path.parent / target).resolve()
                try:
                    relative = resolved.relative_to(self.root)
                except ValueError:
                    errors.append(f"outside:{ref}:{target}")
                    continue
                if set(relative.parts) & PROTECTED_SEGMENTS:
                    errors.append(f"protected_link:{ref}:{target}")
                elif not resolved.exists():
                    errors.append(f"missing_link:{ref}:{target}")
        return errors, links

    def verify(self) -> dict[str, Any]:
        started = time.perf_counter()
        scan = self.scan()
        errors, links = self._document_errors()
        for path in (self.root / "src" / "file_data").glob("*.py"):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (SyntaxError, UnicodeDecodeError) as exc:
                errors.append(f"python:{path.relative_to(self.root).as_posix()}:{exc}")
        for path in (self.root / "schemas").glob("*.json"):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                errors.append(f"schema:{path.relative_to(self.root).as_posix()}:{exc}")
        protected_changes = [
            path for path in self.git_status_paths() if set(Path(path).parts) & {"inputs", "outputs"}
        ]
        errors.extend(f"protected_change:{path}" for path in protected_changes)
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        document_map = (self.root / "docs" / "obsidian" / "DOCUMENT_MAP.md").read_text(encoding="utf-8")
        if "SESSION_HANDOFF.md" not in readme or "SESSION_HANDOFF.md" not in document_map:
            errors.append("current_state_link_missing")
        if "GENERATED_DOCUMENT_INVENTORY.md" not in document_map:
            errors.append("generated_inventory_link_missing")
        if not scan["ok"]:
            errors.append("maintenance_scan_attention_required")
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        return {
            "ok": not errors,
            "status": "pass" if not errors else "fail",
            "errors": sorted(errors),
            "metrics": {
                "documents": len(self.document_refs(include_generated=True)),
                "links": links,
                "python_files": len(list((self.root / "src" / "file_data").glob("*.py"))),
                "schemas": len(list((self.root / "schemas").glob("*.json"))),
                "elapsed_ms": elapsed,
                "runtime_warning": elapsed > RUNTIME_WARNING_MS,
            },
            "scan": scan,
        }

    def evaluate_context(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping) or set(payload) != {"evaluations"}:
            raise MaintenanceError("evaluation payload must contain exactly evaluations")
        evaluations = payload["evaluations"]
        if not isinstance(evaluations, list) or not evaluations:
            raise MaintenanceError("evaluations must be a non-empty list")
        baseline = self.context.measure_documents(self.document_refs(include_generated=True))
        results: list[dict[str, Any]] = []
        for evaluation in evaluations:
            required = {
                "name", "request", "expected_record_ids", "forbidden_record_ids",
                "max_characters", "min_reduction_percent", "max_irrelevant_records",
            }
            if not isinstance(evaluation, Mapping) or set(evaluation) != required:
                raise MaintenanceError(f"each evaluation must contain exactly: {sorted(required)}")
            request = dict(evaluation["request"])
            request["baseline_characters"] = baseline["characters"]
            first = self.context.build_package(request)
            second = self.context.build_package(request)
            selected_ids = {
                item["id"] for item in first["selected"] if item["kind"] == "record"
            }
            expected = set(evaluation["expected_record_ids"])
            forbidden = set(evaluation["forbidden_record_ids"])
            missing = sorted(expected - selected_ids)
            forbidden_found = sorted(forbidden & selected_ids)
            irrelevant = sorted(selected_ids - expected)
            checks = {
                "required_present": not missing,
                "forbidden_absent": not forbidden_found,
                "irrelevant_within_limit": len(irrelevant) <= evaluation["max_irrelevant_records"],
                "size_within_limit": first["metrics"]["content_characters"] <= evaluation["max_characters"],
                "reduction_met": first["metrics"]["reduction_percent"]
                >= evaluation["min_reduction_percent"],
                "repeatable": first == second,
            }
            results.append(
                {
                    "name": evaluation["name"],
                    "ok": all(checks.values()),
                    "checks": checks,
                    "missing_record_ids": missing,
                    "forbidden_record_ids": forbidden_found,
                    "irrelevant_record_ids": irrelevant,
                    "metrics": first["metrics"],
                    "fingerprint": first["fingerprint"],
                }
            )
        return {
            "ok": all(result["ok"] for result in results),
            "baseline": baseline,
            "results": results,
        }
