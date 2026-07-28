"""Non-persistent KPI aggregation for workflow learning.

Only numeric work metadata is accepted.  Raw media, source text, protected
paths, and per-job reports are intentionally outside this module's contract.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from statistics import mean
from typing import Any


KPI_FIELDS = frozenset(
    {
        "job_id",
        "baseline_minutes",
        "actual_minutes",
        "user_revision_minutes",
        "first_pass_accepted",
        "rework_count",
        "automation_steps",
        "manual_steps",
        "approval_wait_minutes",
        "retention",
    }
)
_RETENTION = "aggregate_only"


class MeasurementError(ValueError):
    """Raised when a KPI row crosses the aggregate-only contract."""


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise MeasurementError(f"{field} must be a non-negative number")
    return float(value)


def validate_measurement(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one aggregate-only measurement row."""

    if not isinstance(value, Mapping) or set(value) != KPI_FIELDS:
        raise MeasurementError(f"measurement must contain exactly: {sorted(KPI_FIELDS)}")
    job_id = value["job_id"]
    if not isinstance(job_id, str) or not job_id.strip() or any(char in job_id for char in "\\/\x00"):
        raise MeasurementError("job_id must be a non-empty non-path string")
    first_pass = value["first_pass_accepted"]
    if not isinstance(first_pass, bool):
        raise MeasurementError("first_pass_accepted must be boolean")
    if value["retention"] != _RETENTION:
        raise MeasurementError("retention must be aggregate_only")
    return {
        "job_id": job_id,
        "baseline_minutes": _number(value["baseline_minutes"], "baseline_minutes"),
        "actual_minutes": _number(value["actual_minutes"], "actual_minutes"),
        "user_revision_minutes": _number(
            value["user_revision_minutes"], "user_revision_minutes"
        ),
        "first_pass_accepted": first_pass,
        "rework_count": int(_number(value["rework_count"], "rework_count")),
        "automation_steps": int(_number(value["automation_steps"], "automation_steps")),
        "manual_steps": int(_number(value["manual_steps"], "manual_steps")),
        "approval_wait_minutes": _number(
            value["approval_wait_minutes"], "approval_wait_minutes"
        ),
        "retention": _RETENTION,
    }


def aggregate_measurements(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return a compact aggregate without retaining individual job records."""

    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise MeasurementError("at least one measurement is required")
    normalized = [validate_measurement(row) for row in rows]
    total_steps = sum(row["automation_steps"] + row["manual_steps"] for row in normalized)
    return {
        "sample_count": len(normalized),
        "baseline_minutes_mean": mean(row["baseline_minutes"] for row in normalized),
        "actual_minutes_mean": mean(row["actual_minutes"] for row in normalized),
        "user_revision_minutes_mean": mean(
            row["user_revision_minutes"] for row in normalized
        ),
        "first_pass_acceptance_rate": mean(
            1 if row["first_pass_accepted"] else 0 for row in normalized
        ),
        "rework_count_total": sum(row["rework_count"] for row in normalized),
        "automation_step_share": (
            sum(row["automation_steps"] for row in normalized) / total_steps
            if total_steps
            else 0.0
        ),
        "approval_wait_minutes_total": sum(
            row["approval_wait_minutes"] for row in normalized
        ),
        "retention": _RETENTION,
    }


def audit_complexity(
    aggregate: Mapping[str, Any],
    *,
    minimum_sample_count: int = 3,
) -> dict[str, Any]:
    """Suggest retain, simplify, or defer without changing an active rule."""

    sample_count = aggregate.get("sample_count", 0)
    if not isinstance(sample_count, int) or sample_count < minimum_sample_count:
        return {
            "decision": "defer",
            "reason": "insufficient aggregate sample; no rule change is justified",
            "candidate": None,
        }
    baseline = float(aggregate["baseline_minutes_mean"])
    actual = float(aggregate["actual_minutes_mean"])
    rework = int(aggregate["rework_count_total"])
    if actual < baseline and rework == 0:
        return {
            "decision": "retain",
            "reason": "measured time is lower without aggregate rework",
            "candidate": None,
        }
    return {
        "decision": "candidate",
        "reason": "complexity may have no net effect; review before changing a rule",
        "candidate": "reduce_or_remove_low_effect_automation",
    }
