---
schema_version: 1.0.0
pack_id: validation
kind: conditional_rules
language: en
owner: user-approved, agent-maintained
---

# Validation Rules

- Purpose: Hold task-scoped verification, reporting, failure, and handoff closure rules.
- Use when: Selected for validation, reporting, closure, or handoff work.
- Owner: The user approves policy; project agents maintain accepted records.
- Language: English.
- Location: `rules/validation.md`. Governed by [PROJECT_RULES.md](../PROJECT_RULES.md) and parsed by [context_system.py](../tools/context/context_system.py).

## rule.validation.proportional-verification

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.validation.proportional-verification",
  "text": "Verify changes in proportion to their risk and report the actual validation level: structural, automated, application-validated, or user-approved.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "phase", "op": "in", "value": ["validate", "close"]}, {"field": "task_tags", "op": "intersects", "value": ["validation", "report"]}]},
  "excludes_when": [],
  "phases": ["write", "validate", "close"],
  "task_tags": ["validation", "reporting"],
  "source_refs": ["src.repo.project-rules#6.1"],
  "validators": ["validate.level"]
}
```

## rule.validation.no-overclaim

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.validation.no-overclaim",
  "text": "Do not report generated or test-passing output as content-approved or user-approved.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "output_audience", "op": "eq", "value": "user"}, {"field": "phase", "op": "in", "value": ["validate", "close"]}]},
  "excludes_when": [],
  "phases": ["validate", "close"],
  "task_tags": ["validation", "reporting"],
  "source_refs": ["src.repo.project-rules#6.2"],
  "validators": ["validate.no_overclaim"]
}
```

## rule.validation.failure-record

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.validation.failure-record",
  "text": "Record failures with their objective, confirmed cause, verification result, and next condition when they affect later work.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "task_tags", "op": "intersects", "value": ["failure", "validation"]}, {"field": "phase", "op": "in", "value": ["validate", "close"]}]},
  "excludes_when": [],
  "phases": ["write", "validate", "close"],
  "task_tags": ["validation", "failure"],
  "source_refs": ["src.repo.project-rules#6.3"],
  "validators": ["validate.failure_ledger"]
}
```

## rule.validation.update-handoff

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.validation.update-handoff",
  "text": "At task completion, update the current handoff with verified state and the first unstarted action.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "phase", "op": "in", "value": ["close"]}, {"field": "task_tags", "op": "intersects", "value": ["handoff", "closure"]}]},
  "excludes_when": [],
  "phases": ["validate", "close"],
  "task_tags": ["validation", "handoff"],
  "source_refs": ["src.repo.project-rules#6.4"],
  "validators": ["validate.handoff"]
}
```
