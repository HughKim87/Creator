"""Evidence binding for user-review candidates; never grants semantic approval."""
from collections.abc import Mapping
from datetime import datetime, timezone
from .premiere_xml import PremiereXmlError
from .timeline_v2 import editorial_fingerprint, task_payload_fingerprint
from .editorial_state import editorial_state_fingerprint, validate_editorial_state

CHECKS = frozenset({"source_mapping", "speech_boundaries", "visual_boundaries", "causal_continuity", "feedback_regression"})
FIELDS = frozenset({"version", "editorial_state_fingerprint", "editorial_fingerprint", "task_payload_fingerprint", "reviewer", "checked_at", "checks", "boundary_microbeat_ids", "limitations"})

def validate_preflight(timeline: Mapping, report: Mapping, editorial_state: Mapping) -> None:
    def require(ok, message):
        if not ok:
            raise PremiereXmlError("review preflight: " + message)
    def text(value):
        return isinstance(value, str) and bool(value.strip())
    require(isinstance(report, Mapping) and set(report) == FIELDS, "exact record fields required")
    require(report["version"] == "review-preflight-v2", "unsupported version")
    require(report["editorial_fingerprint"] == editorial_fingerprint(timeline), "stale editorial fingerprint")
    require(report["task_payload_fingerprint"] == task_payload_fingerprint(timeline), "stale task fingerprint")
    require(text(report["reviewer"]), "reviewer required")
    try:
        checked = datetime.fromisoformat(report["checked_at"].replace("Z", "+00:00"))
        revision = datetime.fromisoformat(timeline["revision"]["checked_at"].replace("Z", "+00:00"))
        require(checked.tzinfo is not None and revision <= checked <= datetime.now(timezone.utc), "invalid review chronology")
    except (TypeError, ValueError, AttributeError):
        raise PremiereXmlError("review preflight: timezone-aware timestamp required") from None
    require(report["editorial_state_fingerprint"] == editorial_state_fingerprint(editorial_state), "stale editorial state fingerprint")
    validate_editorial_state(timeline, editorial_state)
    checks = report["checks"]
    require(isinstance(checks, Mapping) and set(checks) == CHECKS, "all five checks required")
    for name, check in checks.items():
        require(isinstance(check, Mapping) and set(check) == {"status", "method", "evidence"}, name + " fields invalid")
        expected = {"passed"} if name == "source_mapping" else {"recorded", "not_run"}
        require(check["status"] in expected and text(check["method"]) and text(check["evidence"]), name + " needs evidence at its actual observation level (not semantic passed)")
    ids = report["boundary_microbeat_ids"]
    expected = {b["id"] for b in timeline["editorial_evidence"]["microbeats"]}
    require(isinstance(ids, list) and all(text(i) for i in ids), "boundary ids required")
    require(len(ids) == len(set(ids)) and set(ids) == expected, "every microbeat needs inspection")
    limits = report["limitations"]
    require(isinstance(limits, list) and bool(limits) and all(text(i) for i in limits), "explicit perceptual review limitations required")
