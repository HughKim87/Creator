#!/usr/bin/env python3
"""Enforce the closed-loop video workflow contract.

This reusable tool validates project state, the rule registry, the edit change
ledger, and promotion claims. ``audit`` checks state coherence without treating
a correctly closed gate as an error. ``assert-transition`` fails when the
requested phase still has unmet evidence or rules.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONTRACT_PATH = Path("docs/WORKFLOW_CONTRACT.json")


class WorkflowGateError(RuntimeError):
    """Raised when a workflow contract file is missing or malformed."""


@dataclass
class GateResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: dict[str, list[str]] = field(default_factory=dict)

    @property
    def coherent(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "coherent": self.coherent,
            "errors": self.errors,
            "warnings": self.warnings,
            "transitions": {
                name: {"allowed": not reasons, "blockers": reasons}
                for name, reasons in self.blockers.items()
            },
        }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise WorkflowGateError(f"required file missing: {path.as_posix()}")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowGateError(f"cannot parse {path.as_posix()}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowGateError(f"JSON root must be an object: {path.as_posix()}")
    return value


def dotted_get(value: dict[str, Any], dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _path(root: Path, value: str) -> Path:
    return root / Path(value)


def _active_rules(registry: dict[str, Any]) -> list[dict[str, Any]]:
    rules = registry.get("rules")
    return [rule for rule in rules if rule.get("status") == "active"] if isinstance(rules, list) else []


def _validate_contract_policies(contract: dict[str, Any], result: GateResult) -> None:
    transition_policy = contract.get("transition_policy")
    if not isinstance(transition_policy, dict) or transition_policy.get(
        "require_immediate_predecessor_approval"
    ) is not True:
        result.errors.append("workflow contract must require immediate predecessor approval")

    calibration = contract.get("calibration_policy")
    if not isinstance(calibration, dict):
        result.errors.append("workflow contract missing calibration_policy")
    else:
        positions = calibration.get("required_positions")
        if not isinstance(positions, list) or set(positions) != {"opening", "middle", "ending"}:
            result.errors.append("calibration_policy must cover opening, middle, and ending")
        checks = calibration.get("agent_checks_before_user")
        required_checks = {"actual_av_playback", "speech_boundaries", "message_visible_without_review_metadata"}
        if not isinstance(checks, list) or not required_checks.issubset(checks):
            result.errors.append("calibration_policy is missing required agent prechecks")
        if calibration.get("recommended_packages_shown_to_user") != 1:
            result.errors.append("calibration_policy must show one recommended package")
        if calibration.get("user_checkpoint_count_before_full_expansion") != 1:
            result.errors.append("calibration_policy must use one user checkpoint before full expansion")
        if calibration.get("full_edit_before_user_checkpoint") is not False:
            result.errors.append("calibration_policy must forbid full edit before the user checkpoint")
        if calibration.get("mp4_requires_current_request_authorization") is not True:
            result.errors.append("calibration_policy must require current-request MP4 authorization")

    routing = contract.get("revision_routing")
    required_routes = {
        "message_or_viewer_promise",
        "rhythm_or_comedy",
        "local_cut_or_boundary",
        "source_fingerprint_or_target_audience_changed",
    }
    if not isinstance(routing, dict) or not required_routes.issubset(routing):
        result.errors.append("workflow contract missing revision_routing entries")
    elif any(not isinstance(routing[key], list) or not routing[key] for key in required_routes):
        result.errors.append("workflow contract revision_routing entries must be non-empty arrays")


def _transition_blockers(
    target: str,
    contract: dict[str, Any],
    state: dict[str, Any],
    registry: dict[str, Any],
) -> list[str]:
    transition = contract.get("transitions", {}).get(target)
    if not isinstance(transition, dict):
        return [f"unknown transition: {target}"]

    phase_order = contract.get("phase_order", [])
    try:
        target_index = phase_order.index(target)
    except ValueError:
        return [f"target is not in phase_order: {target}"]

    blockers = []
    if contract.get("transition_policy", {}).get("require_immediate_predecessor_approval") is True:
        previous_phase = phase_order[target_index - 1] if target_index else None
        if previous_phase and dotted_get(state, f"phases.{previous_phase}.approved_for_next_phase") is not True:
            blockers.append(f"previous phase not approved: {previous_phase}")
    for requirement in transition.get("requires", []):
        if dotted_get(state, requirement) is not True:
            blockers.append(f"state requirement not passed: {requirement}")
    for rule in _active_rules(registry):
        required_before = rule.get("required_before")
        if required_before not in phase_order:
            blockers.append(f"{rule.get('id', '<unknown>')}: invalid required_before={required_before}")
            continue
        if phase_order.index(required_before) <= target_index and rule.get("verification_status") != "passed":
            blockers.append(
                f"rule not passed: {rule.get('id', '<unknown>')} ({rule.get('verification_status')})"
            )
    return blockers


def audit_project(root: Path) -> GateResult:
    result = GateResult()
    try:
        contract = load_json(root / CONTRACT_PATH)
        state = load_json(_path(root, contract["state_path"]))
        registry = load_json(_path(root, contract["rule_registry_path"]))
        ledger = load_json(_path(root, contract["edit_change_ledger_path"]))
    except (KeyError, WorkflowGateError) as exc:
        result.errors.append(str(exc))
        return result

    if contract.get("schema_version") != 1:
        result.errors.append("unsupported workflow contract schema_version")
    if state.get("schema_version") != 1:
        result.errors.append("unsupported workflow state schema_version")
    if registry.get("schema_version") != 1:
        result.errors.append("unsupported rule registry schema_version")
    if ledger.get("schema_version") != 1:
        result.errors.append("unsupported edit ledger schema_version")
    _validate_contract_policies(contract, result)

    source_ids = {state.get("source_id"), registry.get("source_id"), ledger.get("source_id")}
    if None in source_ids or len(source_ids) != 1:
        result.errors.append(f"source_id mismatch across state, registry, and ledger: {sorted(map(str, source_ids))}")

    required_fields = set(contract.get("required_rule_fields", []))
    valid_statuses = set(contract.get("verification_statuses", []))
    rules = registry.get("rules")
    if not isinstance(rules, list):
        result.errors.append("rule registry field 'rules' must be an array")
        rules = []
    seen_ids: set[str] = set()
    for index, rule in enumerate(rules, 1):
        if not isinstance(rule, dict):
            result.errors.append(f"rule {index} must be an object")
            continue
        missing = sorted(required_fields - set(rule))
        if missing:
            result.errors.append(f"rule {index} missing fields: {', '.join(missing)}")
        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not rule_id:
            result.errors.append(f"rule {index} has no valid id")
        elif rule_id in seen_ids:
            result.errors.append(f"duplicate rule id: {rule_id}")
        else:
            seen_ids.add(rule_id)
        verification_status = rule.get("verification_status")
        if verification_status not in valid_statuses:
            result.errors.append(f"{rule_id or index}: invalid verification_status={verification_status}")
        evidence = rule.get("evidence")
        if verification_status == "passed" and (not isinstance(evidence, list) or not evidence):
            result.errors.append(f"{rule_id or index}: passed rule requires evidence")
        if isinstance(evidence, list):
            for evidence_path in evidence:
                if not isinstance(evidence_path, str) or not _path(root, evidence_path).exists():
                    result.errors.append(f"{rule_id or index}: evidence path missing: {evidence_path}")

    approved_baseline = state.get("approved_edit_baseline")
    if approved_baseline != ledger.get("approved_baseline"):
        result.errors.append("approved baseline differs between workflow state and edit ledger")
    lock_released = state.get("generation_lock_released") is True
    generation_allowed = ledger.get("generation_allowed") is True
    if lock_released != generation_allowed:
        result.errors.append("generation lock differs between workflow state and edit ledger")
    if approved_baseline is None and lock_released:
        result.errors.append("generation lock cannot be released without an approved baseline")
    calibration_allowed = state.get("calibration_generation_allowed")
    if not isinstance(calibration_allowed, bool):
        result.errors.append("workflow state calibration_generation_allowed must be a boolean")

    phase_order = contract.get("phase_order", [])
    phases = state.get("phases", {})
    earlier_closed = False
    for phase in phase_order:
        phase_state = phases.get(phase)
        if not isinstance(phase_state, dict):
            result.errors.append(f"workflow state missing phase: {phase}")
            earlier_closed = True
            continue
        approved = phase_state.get("approved_for_next_phase") is True
        if earlier_closed and approved:
            result.errors.append(f"phase approved despite an earlier closed phase: {phase}")
        if not approved:
            earlier_closed = True

    for target in contract.get("transitions", {}):
        result.blockers[target] = _transition_blockers(target, contract, state, registry)

    edit_current_path = root / "outputs/07_edit_export/CURRENT.json"
    if edit_current_path.exists():
        try:
            edit_current = load_json(edit_current_path)
        except WorkflowGateError as exc:
            result.errors.append(str(exc))
        else:
            role = edit_current.get("artifact_role")
            if role not in set(contract.get("artifact_roles", [])):
                result.errors.append(f"edit CURRENT has unsupported artifact_role: {role}")
            if role == "current_deliverable" and result.blockers.get("final"):
                result.errors.append("edit CURRENT is current_deliverable while the final gate is closed")
            if not lock_released and role in {"approved_baseline", "current_deliverable"}:
                result.errors.append(f"edit CURRENT role {role} conflicts with the generation lock")

    if state.get("mode") == "workflow_recovery" and lock_released:
        result.errors.append("workflow_recovery mode cannot have generation lock released")
    if result.coherent and all(result.blockers.values()):
        result.warnings.append("all forward transitions are correctly closed; recovery work only")
    return result


def render_text(result: GateResult, target: str | None = None) -> str:
    lines = ["WORKFLOW GATE AUDIT", f"- coherent: {result.coherent}"]
    if result.errors:
        lines.append("- errors:")
        lines.extend(f"  - {item}" for item in result.errors)
    if result.warnings:
        lines.append("- warnings:")
        lines.extend(f"  - {item}" for item in result.warnings)
    transitions = [target] if target else list(result.blockers)
    for name in transitions:
        blockers = result.blockers.get(name, [f"unknown transition: {name}"])
        lines.append(f"- transition {name}: {'BLOCKED' if blockers else 'ALLOWED'}")
        lines.extend(f"  - {item}" for item in blockers)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit and enforce closed-loop video workflow gates.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("audit")
    assertion = commands.add_parser("assert-transition")
    assertion.add_argument("--to", required=True)
    args = parser.parse_args(argv)

    result = audit_project(args.root.resolve())
    target = args.to if args.command == "assert-transition" else None
    if args.json:
        payload = result.to_dict()
        if target:
            payload["requested_transition"] = target
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(result, target))

    if not result.coherent:
        return 1
    if target and result.blockers.get(target, ["unknown transition"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
